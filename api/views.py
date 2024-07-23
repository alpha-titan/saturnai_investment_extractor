import json
import logging
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from django.conf import settings
from .serializers import FileUploadSerializer, FinancialDataSerializer
from .models import FinancialData

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

openai_api_key = settings.OPENAI_API_KEY
model = ChatOpenAI(model_name="gpt-4o", api_key=openai_api_key, temperature=0.0)

class FinancialDataSchema(BaseModel):
    assets: list[str] = Field(description="Sentences which indicates assets and convert each sentence to third person perspective")
    expenditures: list[str] = Field(description="Sentences which indicates expenditures and convert each sentence to third person perspective")
    income: list[str] = Field(description="Sentences which indicates income sources and convert each sentence to third person perspective")
    client_name: str = Field(description="Name of the client")
    advisor_name: str = Field(description="Name of the advisor")

parser = PydanticOutputParser(pydantic_object=FinancialDataSchema)

prompt = PromptTemplate(
    template="Extract the following financial details from the conversation:\n{format_instructions}\n{query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


'''
    The Main constraint here is what if the file is too large and llm can throw an error, for this we chunk the data\
    
    There can be two approaches here we can either split the file size on a hard threshold and process it or we can 
    split them in a hard threshold and intelligently parse them by only taking parts which lies in the threshold

    the .txt file which is bieng uploaded has an interesting pattern, which is [END OF PART X][BEGIN TRANSCRIPT].

    we can split them Based on "[END OF PART " to get the part

'''
def chunk_text(text, max_chunk_size=5000):
    parts = text.split("[End of Part ")
    chunks = []
    current_chunk = ""
    for i, part in enumerate(parts):
        if i != 0:
            part = "[End of Part " + part
        if len(current_chunk) + len(part) > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = part
        else:
            current_chunk += part
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def extract_financial_data_from_chunk(chunk):
    prompt_text = prompt.format(query=chunk)
    response = model.invoke(prompt_text)
    output_text = response.content.strip()
    financial_data_raw = parser.parse(output_text)
    return financial_data_raw.dict()

def merge_financial_data(data_list):
    merged_data = {
        "client_name": data_list[0]["client_name"],
        "advisor_name": data_list[0]["advisor_name"],
        "assets": [],
        "expenditures": [],
        "income": [],
    }
    for data in data_list:
        merged_data["assets"].extend(data.get("assets", []))
        merged_data["expenditures"].extend(data.get("expenditures", []))
        merged_data["income"].extend(data.get("income", []))
    return merged_data

class TranscriptUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        logger.info("Received request to extract financial data")
        file_serializer = FileUploadSerializer(data=request.data)
        if file_serializer.is_valid():
            file = request.FILES['file']
            try:
                conversation_text = file.read().decode('utf-8')
            except Exception as e:
                logger.error("Failed to read uploaded file", exc_info=True)
                return Response({"error": "Failed to read file"}, status=status.HTTP_400_BAD_REQUEST)

            if len(conversation_text) > 10000: 
                logger.info("File too large, splitting into chunks")
                chunks = chunk_text(conversation_text)
                financial_data_list = []
                for chunk in chunks:
                    try:
                        financial_data = extract_financial_data_from_chunk(chunk)
                        financial_data_list.append(financial_data)
                    except Exception as e:
                        logger.error("Failed to extract financial data from chunk", exc_info=True)
                        return Response({"error": "Failed to process chunk"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                merged_data = merge_financial_data(financial_data_list)
            else:
                logger.info("Processing single chunk")
                try:
                    merged_data = extract_financial_data_from_chunk(conversation_text)
                except Exception as e:
                    logger.error("Failed to extract financial data", exc_info=True)
                    return Response({"error": "Failed to extract financial data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            for key in ['assets', 'expenditures', 'income']:
                if isinstance(merged_data[key], str):
                    try:
                        merged_data[key] = json.loads(merged_data[key].replace("'", '"'))
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON for {key}", exc_info=True)
                        return Response({"error": f"Failed to decode JSON for {key}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                financial_data = FinancialData.objects.create(**merged_data)
            except Exception as e:
                logger.error("Failed to save data to the database", exc_info=True)
                return Response({"error": "Failed to save data to the database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            serializer = FinancialDataSerializer(financial_data)
            logger.info("Successfully extracted and saved financial data")
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            logger.warning("Invalid file upload request")
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)