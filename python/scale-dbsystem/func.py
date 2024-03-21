import io
import json
import oci
import logging

from fdk import response

def scaling_db_system(db_system_id):
    logging.getLogger().info("begin scale storage up, dbsystem id=" + db_system_id)
    update_db_system_response = "failed to scale up"
    signer = oci.auth.signers.get_resource_principals_signer()
    database_client = oci.database.DatabaseClient({}, signer = signer)
    
    try:
        update_db_system_response = database_client.update_db_system(
            db_system_id=db_system_id,
            update_db_system_details=oci.database.models.UpdateDbSystemDetails(
                data_storage_size_in_gbs=512,
                reco_storage_size_in_gbs=256)
            )
    except Exception as ex:
        logging.getLogger().error('failed to scale storage up, ' + str(ex))
        raise
        
    return update_db_system_response

def handler(ctx, data: io.BytesIO = None):
    db_system_id = None
    try:
        body = json.loads(data.getvalue())
        type = body.get("type")
        if("OK_TO_FIRING"!=type):
            return
        alarmMetaData = body.get("alarmMetaData")[0]
        dimensions = alarmMetaData.get("dimensions")[0]
        db_system_id = dimensions.get("resourceId")
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error parsing json payload: ' + str(ex))
        raise
    
    if(db_system_id is None):
        logging.getLogger().error('cannot get dbsystem id from body' + body)
        return

    result = scaling_db_system(db_system_id=db_system_id)

    logging.getLogger().info("successfully complete the scale storage up")
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "{0}".format(result)}),
        headers={"Content-Type": "application/json"}
    )
