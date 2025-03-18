from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from models.user import UserPaymentInfo
from llama_index.core.tools import FunctionTool

supabase = create_client(supabase_key=SUPABASE_SERVICE_KEY, supabase_url=SUPABASE_URL)

def create_payment_link(email: str, username: str, phone_number: str, amount: str) -> str:
    try:
        user_info = UserPaymentInfo(
            email=email, username=username, amount=amount, phone_number=phone_number
        )
        result = supabase.table("payments").insert([{
            "email": user_info.email,
            "username": user_info.username,
            "amount": user_info.amount,
            "phone_number": user_info.phone_number
        }]).execute()
        payment_id = result.data[0]["id"]
        payment_link_url = "http://www.fourier.com/payment/ADF321"
        return f"Payment link created successfully: {payment_link_url} your payment id is {payment_id}"
    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error creating payment link: {str(e)}"

payment_link_tool = FunctionTool.from_defaults(
    name="create_payment_link",
    description="Create a payment link and store user information in the database",
    fn=create_payment_link
)