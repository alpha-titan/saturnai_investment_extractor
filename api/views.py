import json
import logging
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer, FinancialDataSerializer
from .models import FinancialData
from .utils import chunk_text, extract_financial_data_from_chunk, merge_financial_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
