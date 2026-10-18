from datetime import date

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
client = Anthropic()


# 1. The shape we want back, just like DocumentIn in Week 1
class RatesNotice(BaseModel):
    council: str
    property_address: str
    assessment_number: str | None = None
    amount_due: float = Field(description="Total amount payable in AUD")
    due_date: date
    discount_amount: float | None = Field(None, description="Early payment discount in AUD, if shown")


# 2. A sample notice (made up; later this text comes from a real PDF)
NOTICE = """
MORETON BAY CITY COUNCIL
Rates and Charges Notice: half year 1 July to 31 December 2026
Assessment number: 1234567
Property: 12 Example Street, Warner QLD 4500
General rates                 $812.40
Waste management charge       $236.10
Water access charge           $151.00
Total amount payable          $1,199.50
Due date: 30 November 2026
Pay by the due date to receive a discount of $40.60
"""

# 3. Ask Claude to fill the shape
response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=500,
    system="Extract data from Australian council rates notices. Use only values printed on the notice.",
    tools=[{
        "name": "save_rates_notice",
        "description": "Save the fields extracted from a rates notice.",
        "input_schema": RatesNotice.model_json_schema(),
    }],
    tool_choice={"type": "tool", "name": "save_rates_notice"},
    messages=[{"role": "user", "content": NOTICE}],
)

# 4. Validate what came back
notice = RatesNotice.model_validate(response.content[0].input)

print(notice)
print(f"Due {notice.due_date:%d %b %Y}: ${notice.amount_due:,.2f}")