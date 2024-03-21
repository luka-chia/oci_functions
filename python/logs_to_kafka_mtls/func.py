import io
import json
import logging
import oci
import base64
from confluent_kafka import Producer, KafkaError

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("2222=========================================================")
    cfg = ctx.Config()
    signer = oci.auth.signers.get_resource_principals_signer()
    try:
        topic_name = str(cfg["topic_name"])
        bootstrap_server = str(cfg["bootstrap_server"])
        security_protocol = str(cfg["security_protocol"])
        secret_name = str(cfg["ca_cert_secret_name"])
        client_cert_secret = str(cfg["client_cert_secret_name"])
        vauld_ocid = str(cfg["vauld_ocid"])
    except:
        logging.error('Some of the function config keys are not set')
        raise
    try:
        body = json.loads(data.getvalue())
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))
    try:
        client_certificate = decodeSecret(
        p_signer=signer, p_secretName=client_cert_secret, p_vaultOCID=vauld_ocid)
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error retrieving the client certificate from vault: ' + str(ex))
    try:
        decoded_secret = decodeSecret(
            p_signer=signer, p_secretName=secret_name, p_vaultOCID=vauld_ocid)
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error retrieving the secret: ' + str(ex))
    try:
        sent_logs = publish_message(topic=topic_name, bootstrap_srv=bootstrap_server, security_protocol=security_protocol,
                         ca_pem=decoded_secret, client_pem=client_certificate, record_value=bytes(str(body[0]), encoding='utf-8'))
        logging.info(f'log is sent {sent_logs}')
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error in publishing the message: ' + str(ex))

def decodeSecret(p_signer, p_secretName, p_vaultOCID):
    secretClient = oci.secrets.SecretsClient(config={}, signer=p_signer)
    secret = secretClient.get_secret_bundle_by_name(
                                secret_name=p_secretName, vault_id=p_vaultOCID).data
    secret_content = secret.secret_bundle_content.content.encode("utf-8")
    decodedSecret = base64.b64decode(secret_content).decode("utf-8")
    return decodedSecret

def delivery_report(errmsg, msg):
    if errmsg is not None:
        print("Delivery failed for Message: {} : {}".format(msg.key(), errmsg))
        return
    print('Message successfully produced to Topic:{} at offset {}'.format(
            msg.topic(), msg.offset()))

def publish_message(topic, bootstrap_srv, security_protocol, ca_pem, client_pem, record_value):
    conf = {
        'bootstrap.servers': bootstrap_srv,
        'security.protocol': security_protocol,
        'ssl.certificate.pem': client_pem,
        'ssl.ca.pem': ca_pem
    }
    producer = Producer(conf)
    produce_log = producer.produce(topic, key=None, value=record_value, on_delivery=delivery_report)
    producer.flush()
    return produce_log
