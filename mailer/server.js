const express = require('express');
const nodemailer = require('nodemailer');
const cors = require('cors');
const app = express();
app.use(express.json());
app.use(cors({ origin: '*' }));

const transporter = nodemailer.createTransport({
  host: 'smtpout.secureserver.net',
  port: 465,
  secure: true,
  auth: {
    user: 'divyam@datacatalyst.in',
    pass: 'Jayanshu1@'
  }
});

app.post('/send', async (req, res) => {
  const { name, email, company, use_case, volume, notes } = req.body;
  if (!name || !email || !company) return res.status(400).json({ error: 'Missing fields' });

  const signature = `\n\n──────────────────────────────\nDivyam Bhatia\nFounder & CEO, DataCatalyst\ndatacatalyst.in\nJaipur, Rajasthan, India\n──────────────────────────────`;

  try {
    await transporter.sendMail({
      from: 'divyam@datacatalyst.in',
      to: 'divyam@datacatalyst.in',
      subject: `New Sample Request from ${name}`,
      text: `You have a new sample dataset request!\n\nName: ${name}\nEmail: ${email}\nCompany: ${company}\nUse Case: ${use_case}\nVolume: ${volume}\nNotes: ${notes}${signature}`
    });
    await transporter.sendMail({
      from: 'divyam@datacatalyst.in',
      to: email,
      subject: "We've received your request — DataCatalyst",
      text: `Hi ${name},\n\nThis is an automated confirmation email.\n\nYour sample dataset request has been received. Our team will review your requirements and get back to you within 48 hours.${signature}`
    });
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to send email' });
  }
});

app.listen(3000, () => console.log('Mailer running on port 3000'));
