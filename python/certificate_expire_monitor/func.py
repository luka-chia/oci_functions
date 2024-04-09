import io
import json
import logging
import oci
import base64

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("begin ================================================================================")
    cfg = ctx.Config()
    signer = oci.auth.signers.get_resource_principals_signer()
    try:
        topic_id = str(cfg["topic_id"])
    except:
        logging.getLogger().error('Some of the function config keys are not set')
        raise
    try:
        certificates_management_client = oci.certificates_management.CertificatesManagementClient({}, signer = signer)
        # Send the request to service, some parameters are not required, see API doc for more info
        list_certificates_response = certificates_management_client.list_certificates(
            compartment_id="ocid1.compartment.oc1..aaaaaaaajyvcxbeipsa5s4jgzdi7o3oztfqpgxickubwkajwku5hfh4octoq"
            )

        # Get the data from response
        certificates = list_certificates_response.data
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error in publishing the message: ' + str(ex))

def publish_notification(topic_id, msg_title, body):
    try:
        topic_id = topic_id
        msg_title = "certificate expire alarm"
        msg_body = json.dumps(body)
        logging.getLogger().info(f"send message [{msg_body}] to topic [{topic_id}]")
        signer = oci.auth.signers.get_resource_principals_signer()
        client = oci.ons.NotificationDataPlaneClient({}, signer = signer)
        msg = oci.ons.models.MessageDetails(title = msg_title, body = msg_body)
        print(msg, flush=True)
        client.publish_message(topic_id, msg)
    except Exception as ex:
        logging.getLogger().error("Three arguments need to be passed to the function, topic_id, msg_title and msg_body", ex, flush=True)
        raise
