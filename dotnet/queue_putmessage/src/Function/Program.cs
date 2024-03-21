using Fnproject.Fn.Fdk;
using Oci.Common.Auth;
using Oci.Common;
using Oci.QueueService;
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
[assembly:InternalsVisibleTo("Function.Tests")]
namespace Function {
	class Greeter {
		public async Task<string> greet(string input) {
            string message_body = string.IsNullOrEmpty(input) ? "this is a test message" : input.Trim();

            var putMessagesDetails = new Oci.QueueService.Models.PutMessagesDetails
            {
                Messages = new List<Oci.QueueService.Models.PutMessagesDetailsEntry>
                {
                    new Oci.QueueService.Models.PutMessagesDetailsEntry
                    {
                        Content = message_body
                    }
                }
            };
            string QueueIdf = "ocid1.queue.oc1.ap-singapore-1.amaaaaaaak7gbriasgcvabpudhvzmaeeacw3nvclv2rtkk2f6sft3iqwaomq";

            var putMessagesRequest = new Oci.QueueService.Requests.PutMessagesRequest
            {
                QueueId = QueueIdf,
                PutMessagesDetails = putMessagesDetails,
                OpcRequestId = "0M20ZFHD84BUPN2UD4JD<udnique_ID>"
            };

            // push message to queue
            var provider = ResourcePrincipalAuthenticationDetailsProvider.GetProvider();
            
            try
            {
                // Create a service client and send the request.
                using (var client = new QueueClient(provider, new ClientConfiguration()))
                {
                    client.SetEndpoint("https://cell-1.queue.messaging.ap-singapore-1.oci.oraclecloud.com");

                    var response = await client.PutMessages(putMessagesRequest);
                    // Retrieve value from the response.
                    //var messagesValue = response.PutMessages.Messages;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"PutMessages Failed with {e.Message}");
                throw e;
            }
			return string.Format("push message {0} to queue {1}!",message_body,Environment.GetEnvironmentVariable("OCI_RESOURCE_PRINCIPAL_VERSION"));
		}

		static void Main(string[] args) { Fdk.Handle(args[0]); }
	}
}
