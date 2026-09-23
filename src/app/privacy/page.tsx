import Link from 'next/link'

export default function Privacy(){
  return <main className="legal-page">
    <Link href="/">← ABHI AGANCY</Link>
    <h1>Privacy Policy</h1>
    <p className="legal-updated">Last updated: September 23, 2026</p>
    <section><h2>Information we collect</h2><p>When you submit an application, ABHI AGANCY may collect the contact and profile information you choose to provide, including your name, country, languages, social-media usernames, messaging contacts, live-streaming platform information, referral code, availability and introduction.</p></section>
    <section><h2>Age requirement</h2><p>The application is intended only for people aged 18 or older. Do not submit the form if you are under 18.</p></section>
    <section><h2>How we use information</h2><p>We use submitted information to review applications, contact applicants, provide onboarding and agency support, administer referral attribution, and understand recruitment performance.</p></section>
    <section><h2>Sensitive documents</h2><p>Do not upload or send passports, government identity documents, banking credentials, passwords, or other highly sensitive documents through the public application form.</p></section>
    <section><h2>Sharing and retention</h2><p>Application information may be accessible to authorized ABHI AGANCY managers and service providers used to operate the website and applicant database. Information should be retained only as long as reasonably needed for recruitment, agency operations, legal obligations, and dispute resolution.</p></section>
    <section><h2>Your choices</h2><p>You may contact ABHI AGANCY through the contact methods shown on the website to request correction or deletion of application data, subject to applicable legal requirements.</p></section>
    <section><h2>Changes</h2><p>This policy may be updated when agency processes, technology, or legal requirements change.</p></section>
  </main>
}
