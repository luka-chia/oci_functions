import io
import json
import oci
from fdk import response

def put_queue_message(message):
    # two parameters needed to define oci queue client 
    service_endpoint = "https://cell-1.queue.messaging.ap-singapore-1.oci.oraclecloud.com"
    queue_id="ocid1.queue.oc1.ap-singapore-1.amaaaaaaak7gbriasgcvabpudhvzmaeeacw3nvclv2rtkk2f6sft3iqwaomq"

    # initial the oci queue client
    signer = oci.auth.signers.get_resource_principals_signer()
    queue_client = oci.queue.QueueClient({}, signer = signer,service_endpoint=service_endpoint)
    
    # put message to queue
    put_messages_response = queue_client.put_messages(
        queue_id=queue_id,
        put_messages_details=oci.queue.models.PutMessagesDetails(
        messages=[oci.queue.models.PutMessagesDetailsEntry(content=message)]),
        opc_request_id="0M20ZFHD84BUPN2UD4JD<unique_ID>")

def handler(ctx, data: io.BytesIO = None):
    try:
        msg_body = data.getvalue().decode('UTF-8')
    except Exception as ex:
        print("json parse the data error", ex, flush=True)
        raise
    put_queue_message(msg_body)
    return response.Response(ctx,
        response_data={"response":msg_body},
        headers={"Content-Type": "application/json"}
    )   