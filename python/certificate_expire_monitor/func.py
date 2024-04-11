import io
import json
import logging
import oci
import base64
from datetime import datetime
from fdk import response

def get_imported_certificates(all_regions, all_compartments):
    imported_certificates = list()
    signer = oci.auth.signers.get_resource_principals_signer()
    try:
        for region in all_regions:
            certificates_management_client = oci.certificates_management.CertificatesManagementClient({"region": region}, signer = signer)
            for compartment in all_compartments:
                # Send the request to service, some parameters are not required, see API doc for more info
                compartment_id = compartment.get("id")
                logging.getLogger().info("begin get certificates in region={0} and id={1}".format(region, compartment_id))
                list_certificates_response = certificates_management_client.list_certificates(compartment_id=compartment_id)

                # Get the data from response
                certificates = list_certificates_response.data.items
                for certificate in certificates:
                    if certificate.config_type == "IMPORTED":
                        today = datetime.now().date()
                        cert_expiry_date = certificate.current_version_summary.validity.time_of_validity_not_after
                        remaining_days = cert_expiry_date.date()-today

                        imported_certificate = {
                            "certificate_name": certificate.name,
                            "region": region,
                            "compartment": certificate.compartment_id,
                            "certificate_expiry_date": cert_expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "remaining_days_before_expiry": remaining_days.days
                        }
                        imported_certificates.append(imported_certificate)

        return imported_certificates
    except Exception as ex: 
        logging.getLogger().error('failed to get imported certificates ' + str(ex))
        raise

def get_expiry_certificates(import_certificates, expiration_warning_days):
    logging.getLogger().info('begin get expiry certificates')
    expiry_certificates = list()
    for cert in import_certificates:
        remaining_days = cert.get("remaining_days_before_expiry")
        if remaining_days < int(expiration_warning_days):
            expiry_certificates.append(cert)
    
    return expiry_certificates

def publish_notification(topic_id, msg_title, body, expiration_warning_days):
    logging.getLogger().info('begin to send alarm to notification')
    try:
        msg_begin = f"Dear user\n\nAfter inspection, we found some certificates whose expiration time is less than expiration_warning_days({expiration_warning_days}) from the current time. If the certificate expires and is not updated, it will affect your service. Please check the certificate in advance and handle it. Thank you!\nThese certificates are about to expire as follows:\n\n\n"
        topic_id = topic_id
        msg_title = msg_title
        msg_body = msg_begin + json.dumps(body)
        logging.getLogger().info(f"send message [{msg_body}] to topic [{topic_id}]")
        signer = oci.auth.signers.get_resource_principals_signer()
        client = oci.ons.NotificationDataPlaneClient({}, signer = signer)
        msg = oci.ons.models.MessageDetails(title = msg_title, body = msg_body)
        client.publish_message(topic_id, msg)
    except Exception as ex:
        logging.getLogger().error('error in publishing the alarm about expiry certificate: ' + str(ex))
        raise

def get_all_regions():
    logging.getLogger().info('begin to get all regions')
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.identity.IdentityClient({}, signer = signer)

    # Get all subscribed regions
    subscribedRegionList = client.list_region_subscriptions(signer.tenancy_id)
    all_regions = [c.region_name for c in subscribedRegionList.data]
    
    return all_regions

def get_all_compartments():
    logging.getLogger().info('begin to get all compartments')

    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.identity.IdentityClient(config={}, signer=signer)
    # OCI API for managing users, groups, compartments, and policies
    try:
        # Returns a list of all compartments and subcompartments in the tenancy (root compartment)
        compartments = client.list_compartments(
            signer.tenancy_id,
            compartment_id_in_subtree=True,
            access_level='ANY'
        )
        # Create a list that holds a list of the compartments id and name next to each other
        compartments = [{"id": c.id, "name": c.name } for c in compartments.data]
    except Exception as ex:
        logging.getLogger().error("ERROR: Cannot access compartments" + str(ex))
        raise
    compartments.append({"id": signer.tenancy_id, "name": 'root'})
    return compartments

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("begin to invoke the function")
    cfg = ctx.Config()
    try:
        topic_id = str(cfg["topic_id"])
        expiration_warning_days = cfg["expiration_warning_days"]

        all_regions = get_all_regions()
        logging.getLogger().info(f"all regions count is  [{len(all_regions)}]")

        all_compartments = get_all_compartments()
        logging.getLogger().info(f"all comparements count is [{len(all_compartments)}]")
        
        import_certificates = get_imported_certificates(all_regions=all_regions, all_compartments=all_compartments)

        expiry_certificates = get_expiry_certificates(import_certificates=import_certificates, expiration_warning_days=expiration_warning_days)

        if len(expiry_certificates)>0:
            publish_notification(topic_id=topic_id, msg_title="[critical] An alarm about these expiry certificates", body=expiry_certificates, expiration_warning_days=expiration_warning_days)
        else:
            logging.getLogger().info("currently, there is no expiry certificates")
        logging.getLogger().info("this function invoke is completed")
        return response.Response(ctx,
                                 response_data={"response": expiry_certificates},
                                 headers={"Content-Type": "application/json"})
        
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error in execute this function: ' + str(ex))
        return response.Response(ctx,
                                 response_data={"response": "An error occurred"},
                                 headers={"Content-Type": "application/json"})
