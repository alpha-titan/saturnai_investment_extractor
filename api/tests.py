import os
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from .models import FinancialData
import tempfile

class FinancialDataTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('transcript-upload')
        self.valid_file_content = """
        IFA: Good morning, Mr. Thompson. I'm glad you could make it. My name is Andrew Jenkins, your Independent Financial Advisor. We can start by discussing your financial goals, if that's alright with you?
        Mr. Thompson: Absolutely, Andrew, glad to be here.
        IFA: Excellent. Now, do you have any immediate financial goals that we should be aware of?
        Mr. Thompson: Well, I am looking into purchasing a new property within the next 18 months, possibly in the Kent area.
        IFA: That's an important goal. We'll have to consider your current financial status and your savings for the down payment, property taxes, and the ongoing costs related to property ownership. Do you have a specific budget in mind for the property?
        Mr. Thompson: I've been considering properties around the £500,000 mark. I've saved up about £200,000 so far.
        IFA: That's substantial savings, Mr. Thompson. But as you know, in addition to the down payment, there are other expenses such as stamp duty, solicitor fees, and moving costs. Plus, we need to consider mortgage payments, property maintenance, and insurance costs. All these are important when planning your finances.
        Mr. Thompson: Yes, I understand that. I've been trying to account for those costs, but it's a bit overwhelming.
        IFA: It can seem like a lot, but that's what we're here for. We'll help you navigate these complexities. Now, let's discuss your income and regular expenses to better understand your financial situation.
        [End of Part 1][Begin Transcript]
        IFA: Let's look at your income, Mr. Thompson. Could you share with us your main sources of income and an estimate of how much you're bringing in per month?
        Mr. Thompson: I'm a partner in a law firm here in London. My salary varies, but on average, I would say it's around £15,000 per month before taxes.
        IFA: That's a healthy income. Do you have any other significant sources of income, such as investments, rental income, or a side business?
        Mr. Thompson: I do have a rental property in East London, which brings in about £1,500 per month after expenses.
        IFA: Great, it's important to consider all streams of income when planning your financial future. Now, let's shift to your expenses. Could you give me a rough estimate of your monthly spendings?
        Mr. Thompson: I'd say my monthly expenses, including the mortgage on my current property, bills, and living costs are around £5,000.
        IFA: And how about any outstanding debts or financial obligations? This includes credit cards, loans, or any other form of debts.
        Mr. Thompson: Well, I have a car loan, but that's about £300 a month. And I try to pay off my credit card in full each month. So, no significant debts to speak of.
        IFA: That's good to hear. Managing debt effectively is crucial to maintaining good financial health. But let's not forget about your long-term financial goals. Do you have any retirement plans or savings?
        [End of Part 2][Begin Transcript]
        """
        self.invalid_file_content = "This is an invalid file content"

    def test_valid_file_upload(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.valid_file_content.encode('utf-8'))
            tmp_file.seek(0)
            response = self.client.post(self.url, {'file': tmp_file})
            tmp_file.close()
        os.unlink(tmp_file.name)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FinancialData.objects.count(), 1)
        financial_data = FinancialData.objects.first()
        self.assertEqual(financial_data.client_name, "Mr. Thompson")
        self.assertEqual(financial_data.advisor_name, "Andrew Jenkins")
        
        # Check for substring presence in the assets list items
        self.assertTrue(any("£200,000" in asset for asset in financial_data.assets))
        self.assertTrue(any("£5,000" in expenditure for expenditure in financial_data.expenditures))
        self.assertTrue(any("£15,000" in income for income in financial_data.income))

    def test_invalid_file_upload(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.invalid_file_content.encode('utf-8'))
            tmp_file.seek(0)
            response = self.client.post(self.url, {'file': tmp_file})
            tmp_file.close()
        os.unlink(tmp_file.name)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(FinancialData.objects.count(), 0)
