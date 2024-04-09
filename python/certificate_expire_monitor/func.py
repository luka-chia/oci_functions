import io
import json
import logging
import oci
import base64
from datetime import datetime
from fdk import response

def get_imported_certificates():
    signer = oci.auth.signers.get_resource_principals_signer()
    try:
        certificates_management_client = oci.certificates_management.CertificatesManagementClient({}, signer = signer)
        # Send the request to service, some parameters are not required, see API doc for more info
        list_certificates_response = certificates_management_client.list_certificates(
            compartment_id="ocid1.compartment.oc1..aaaaaaaajyvcxbeipsa5s4jgzdi7o3oztfqpgxickubwkajwku5hfh4octoq"
            )

        # Get the data from response
        certificates = list_certificates_response.data.items
        imported_certificates = list()

        for certificate in certificates:
            if certificate.config_type == "IMPORTED":
                imported_certificates.append(certificate)

        return imported_certificates
    except:
        logging.getLogger().error('failed to get imported certificates')
        raise

def get_expire_certificates(import_certificates, days):
    logging.getLogger().info('begin get expire certificates')
    expire_certificates = list()
    for cert in import_certificates:
        str_date = cert.current_version_summary.validity.time_of_validity_not_after
        today = datetime.now().date()

        remaining_days = str_date.date()-today

        if remaining_days.days < days:
            expire_certificates.append(cert)
        print(remaining_days)

    return expire_certificates

def publish_notification(topic_id, msg_title, body):
    logging.getLogger().info('begin send alarm to notification')
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
    except Exception:
        raise

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("begin ================================================================================")
    cfg = ctx.Config()
    try:
        topic_id = str(cfg["topic_id"])
        days = cfg["days"]

        import_certificates = get_imported_certificates()
        expire_certificates = get_expire_certificates(import_certificates=import_certificates, days=days)
        publish_notification(topic_id=topic_id, msg_title="alert", body=expire_certificates)

        return response.Response(ctx,
        response_data={"response": expire_certificates},
        headers={"Content-Type": "application/json"})
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error in publishing the alarm about expiry certificate: ' + str(ex))
        return response.Response(ctx,
        response_data={"response": "error"},
        headers={"Content-Type": "application/json"})