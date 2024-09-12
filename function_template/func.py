#
# oci-ons-publish-python version 1.0.
#
# Copyright (c) 2020 Oracle, Inc.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#

import io
import json
import oci
from fdk import response


def publish_notification(topic_id, msg_title, msg_body):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.ons.NotificationDataPlaneClient({}, signer = signer)
    msg = oci.ons.models.MessageDetails(title = msg_title, body = msg_body)
    print(msg, flush=True)
    client.publish_message(topic_id, msg)

def handler(ctx, data=None):
    try:
        topic_id = "ocid1.onstopic.oc1.ap-singapore-1.aaaaaaaa5x7picrovnolbsuh5uejesq3gcbfss2fszblvpw6oji5aqlqjgyq"
        msg_title = "function notification"
        msg_body = "the notification from function created by Luka"
        print("topic_id: " + topic_id, flush=True)
        print("msg_title: " + msg_title, flush=True)
        print("msg_body: " + msg_body, flush=True)
    except Exception as ex:
        print("Three arguments need to be passed to the function, topic_id, msg_title and msg_body", ex, flush=True)
        raise
    publish_notification(topic_id, msg_title, msg_body)
    return response.Response(ctx,
        response_data={"response":"email sent"},
        headers={"Content-Type": "application/json"}
    )