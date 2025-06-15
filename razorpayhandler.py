import razorpay
import os
import dotenv

dotenv.load_dotenv()


client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))

def create_order(amount, currency="INR", receipt=None):
    """
    Create a Razorpay order.

    :param amount: Amount to be charged in the smallest currency unit (e.g., paise for INR).
    :param currency: Currency code (default is "INR").
    :param receipt: Optional receipt identifier.
    :return: Razorpay order object.
    """
    data = {
        "amount": amount*100,
        "currency": currency,
        "receipt": receipt
    }

    return client.order.create(data=data)


def getapikey()-> str:
    """
    Get the Razorpay API key.

    :return: Razorpay API key.
    """
    return os.getenv("RAZORPAY_KEY_ID")


def verifyPaymentSignature(payment_id, order_id, signature):
    """
    Verify the payment signature.

    :param payment_id: Razorpay payment ID.
    :param order_id: Razorpay order ID.
    :param signature: Signature to verify.
    :return: True if the signature is valid, False otherwise.
    """
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False


def get_payment(    payment_id: str
) -> dict:
    """
    Get payment details from Razorpay.

    :param payment_id: Razorpay payment ID.
    :return: Payment details as a dictionary.
    """
    try:
        return client.payment.fetch(payment_id)

    except Exception as e:
        print(f"Failed to fetch payment details: {e}")
        return {}
