import nodemailer from 'nodemailer';

// Configure transporter based on environment variables
const createTransporter = () => {
  if (process.env.SMTP_SERVICE === 'gmail' || process.env.GMAIL_USER) {
    return nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.GMAIL_USER || 'divyambhatia2219@gmail.com',
        pass: process.env.GMAIL_APP_PASSWORD || 'xykykawbgnswixwf'
      }
    });
  }

  // Default to GoDaddy / Custom SMTP
  return nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtpout.secureserver.net',
    port: Number(process.env.SMTP_PORT) || 465,
    secure: Number(process.env.SMTP_PORT) === 587 ? false : true,
    auth: {
      user: process.env.SMTP_USER || 'divyam@datacatalyst.in',
      pass: process.env.SMTP_PASS || 'Jayanshu1@'
    },
    tls: {
      rejectUnauthorized: false
    }
  });
};

export const handler = async (event) => {
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
    let rawBody = event.body;
    if (event.isBase64Encoded && rawBody) {
      rawBody = Buffer.from(rawBody, 'base64').toString('utf8');
    }
    body = typeof rawBody === 'string' ? JSON.parse(rawBody || '{}') : (rawBody || {});
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
    const transporter = createTransporter();
    const fromAddress = process.env.FROM_EMAIL || (process.env.GMAIL_USER || 'divyam@datacatalyst.in');

    // 1. Notification email to Founder
    await transporter.sendMail({
      from: `"DataCatalyst Web Form" <${fromAddress}>`,
      to: 'divyam@datacatalyst.in',
      subject: `New Sample Request from ${name}`,
      text: `You have a new sample dataset request!\n\nName: ${name}\nEmail: ${email}\nCompany: ${company}\nUse Case: ${use_case || 'Not specified'}\nVolume: ${volume || 'Not specified'}\nNotes: ${notes || ''}${signature}`
    });

    // 2. Confirmation email to Requester
    await transporter.sendMail({
      from: `"DataCatalyst" <${fromAddress}>`,
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
      body: JSON.stringify({ error: 'Failed to send email', details: err.message })
    };
  }
};
