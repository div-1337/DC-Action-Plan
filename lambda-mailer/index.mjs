import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";

// Default to us-east-1 where SES identity is verified
const sesRegion = process.env.SES_REGION || "us-east-1";
const sesClient = new SESClient({ region: sesRegion });

export const handler = async (event) => {
  const method = event.requestContext?.http?.method || event.httpMethod;

  const corsHeaders = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS, GET',
    'Access-Control-Allow-Headers': '*'
  };

  // 1. Immediately approve any browser CORS preflight check
  if (method === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: corsHeaders,
      body: JSON.stringify({ message: 'OK' })
    };
  }

  let body = {};
  try {
    let rawBody = event.body;
    if (event.isBase64Encoded && rawBody) {
      rawBody = Buffer.from(rawBody, 'base64').toString('utf8');
    }
    body = typeof rawBody === 'string' ? JSON.parse(rawBody || '{}') : (rawBody || {});
  } catch (parseErr) {
    return {
      statusCode: 400,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Invalid JSON payload' })
    };
  }

  const { name, email, company, use_case, volume, notes } = body;
  if (!name || !email || !company) {
    return {
      statusCode: 400,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Missing required fields' })
    };
  }

  const signature = `\n\n──────────────────────────────\nDivyam Bhatia\nFounder & CEO, DataCatalyst\ndatacatalyst.in\nJaipur, Rajasthan, India\n──────────────────────────────`;
  const senderEmail = process.env.FROM_EMAIL || "divyam@datacatalyst.in";

  try {
    // 2. Send Alert email to Founder (Guaranteed to succeed)
    const alertParams = {
      Source: `DataCatalyst Web Form <${senderEmail}>`,
      Destination: {
        ToAddresses: ["divyam@datacatalyst.in"]
      },
      Message: {
        Subject: {
          Data: `New Sample Request from ${name}`,
          Charset: "UTF-8"
        },
        Body: {
          Text: {
            Data: `You have a new sample dataset request!\n\nName: ${name}\nEmail: ${email}\nCompany: ${company}\nUse Case: ${use_case || 'Not specified'}\nVolume: ${volume || 'Not specified'}\nNotes: ${notes || ''}${signature}`,
            Charset: "UTF-8"
          }
        }
      }
    };
    await sesClient.send(new SendEmailCommand(alertParams));

    // 3. Send Confirmation email to Requester (protected against sandbox blocks)
    try {
      const confirmationParams = {
        Source: `DataCatalyst <${senderEmail}>`,
        Destination: {
          ToAddresses: [email]
        },
        Message: {
          Subject: {
            Data: "We've received your request — DataCatalyst",
            Charset: "UTF-8"
          },
          Body: {
            Text: {
              Data: `Hi ${name},\n\nThis is an automated confirmation email.\n\nYour sample dataset request has been received. Our team will review your requirements and get back to you within 48 hours.${signature}`,
              Charset: "UTF-8"
            }
          }
        }
      };
      await sesClient.send(new SendEmailCommand(confirmationParams));
    } catch (confErr) {
      console.warn("Could not send confirmation to requester (SES Sandbox limit):", confErr.message);
    }

    return {
      statusCode: 200,
      headers: corsHeaders,
      body: JSON.stringify({ success: true })
    };
  } catch (err) {
    console.error("SES Send Error:", err);
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({ error: "Failed to send email", details: err.message })
    };
  }
};
