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
            # Send the request to service, some parameters are not required, see API doc for more info
            # compartment_id = compartment.get("id")
            logging.getLogger().info('begin get certificates in region={} and id={}'.format(region, "compartment_id"))
            list_certificates_response = certificates_management_client.list_certificates(compartment_id="ocid1.compartment.oc1..aaaaaaaajyvcxbeipsa5s4jgzdi7o3oztfqpgxickubwkajwku5hfh4octoq")

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

def get_expiry_certificates(import_certificates, days):
    logging.getLogger().info('begin get expiry certificates')
    expiry_certificates = list()
    for cert in import_certificates:
        remaining_days = cert.get("remaining_days_before_expiry")
        if remaining_days < int(days):
            expiry_certificates.append(cert)
    
    return expiry_certificates

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
        client.publish_message(topic_id, msg)
    except Exception as ex:
        logging.getLogger().error('error in publishing the alarm about expiry certificate: ' + str(ex))
        raise

def get_all_regions():
    logging.getLogger().info('====== get all regions')
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.identity.IdentityClient({}, signer = signer)

    # Get all subscribed regions
    subscribedRegionList = client.list_region_subscriptions(signer.tenancy_id).data
    all_regions = list()
    for region in subscribedRegionList:
        all_regions.append(region.region_name)
    
    return all_regions

def get_all_compartments():
    logging.getLogger().info('====== get all compartments')

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
        print("ERROR: Cannot access compartments", ex, flush=True)
        raise
    compartments.append({"id": signer.tenancy_id, "name": 'root'})
    return compartments

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("begin ================================================================================")
    cfg = ctx.Config()
    try:
        topic_id = str(cfg["topic_id"])
        days = cfg["days"]

        all_regions = get_all_regions()
        logging.getLogger().info(f"all regions count is  [{len(all_regions)}]")

        all_compartments = get_all_compartments()
        logging.getLogger().info(f"all comparements count is [{len(all_compartments)}]")
        
        import_certificates = get_imported_certificates(all_regions=all_regions, all_compartments=all_compartments)

        expiry_certificates = get_expiry_certificates(import_certificates=import_certificates, days=days)

        if len(expiry_certificates)>0:
            publish_notification(topic_id=topic_id, msg_title="alert", body=expiry_certificates)
        else:
            logging.getLogger().info("currently, there is no expiry certificates")

        return response.Response(ctx,
                                 response_data={"response": expiry_certificates},
                                 headers={"Content-Type": "application/json"})
        
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error in execute this function: ' + str(ex))
        return response.Response(ctx,
                                 response_data={"response": "An error occurred"},
                                 headers={"Content-Type": "application/json"})
