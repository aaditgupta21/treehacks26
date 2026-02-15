import Link from "next/link";

export default function Home() {
  return (
    <section className="hero-home">
      <h1 className="hero-headline">
        Shared<br />Intelligence
      </h1>
      <p className="hero-tagline">AI that works as one with your team</p>
      <Link href="/dashboard" className="btn-dashboard">
        Enter
      </Link>
    </section>
  );
}
