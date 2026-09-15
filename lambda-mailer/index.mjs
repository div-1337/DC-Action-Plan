import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: 'smtpout.secureserver.net',
  port: 465,
  secure: true,
  auth: {
    user: process.env.SMTP_USER || 'divyam@datacatalyst.in',
    pass: process.env.SMTP_PASS || 'Jayanshu1@'
  }
});

export const handler = async (event) => {
  // Support both Function URL (direct HTTP) and API Gateway event formats
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  };

  // Handle preflight OPTIONS request
  if (event.requestContext?.http?.method === 'OPTIONS' || event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ message: 'OK' })
    };
  }

  let body = {};
  try {
    body = typeof event.body === 'string' ? JSON.parse(event.body || '{}') : (event.body || {});
  } catch (parseErr) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Invalid JSON payload' })
    };
  }

  const { name, email, company, use_case, volume, notes } = body;
  if (!name || !email || !company) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Missing required fields' })
    };
  }

  const signature = `\n\n──────────────────────────────\nDivyam Bhatia\nFounder & CEO, DataCatalyst\ndatacatalyst.in\nJaipur, Rajasthan, India\n──────────────────────────────`;

  try {
    // 1. Notification email to Divyam
    await transporter.sendMail({
      from: 'divyam@datacatalyst.in',
      to: 'divyam@datacatalyst.in',
      subject: `New Sample Request from ${name}`,
      text: `You have a new sample dataset request!\n\nName: ${name}\nEmail: ${email}\nCompany: ${company}\nUse Case: ${use_case || 'Not specified'}\nVolume: ${volume || 'Not specified'}\nNotes: ${notes || ''}${signature}`
    });

    // 2. Confirmation email to the requester
    await transporter.sendMail({
      from: 'divyam@datacatalyst.in',
      to: email,
      subject: "We've received your request — DataCatalyst",
      text: `Hi ${name},\n\nThis is an automated confirmation email.\n\nYour sample dataset request has been received. Our team will review your requirements and get back to you within 48 hours.${signature}`
    });

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ success: true })
    };
  } catch (err) {
    console.error('Failed to send mail:', err);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Failed to send email' })
    };
  }
};
