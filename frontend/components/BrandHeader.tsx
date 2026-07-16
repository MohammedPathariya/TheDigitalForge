import Image from "next/image";
import Link from "next/link";

export function BrandHeader({ active }: { active: "forge" | "benchmark" }) {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="The Digital Forge home">
        <Image src="/forge-mark.svg" width={44} height={44} alt="" priority />
        <span>the digital forge</span>
      </Link>
      <nav className="site-nav" aria-label="Primary navigation">
        <Link className={active === "forge" ? "nav-link active" : "nav-link"} href="/">
          Forge
        </Link>
        <Link
          className={active === "benchmark" ? "nav-link active" : "nav-link"}
          href="/benchmark"
        >
          Benchmark
        </Link>
        <a
          className="nav-link"
          href="https://github.com/MohammedPathariya/TheDigitalForge"
          target="_blank"
          rel="noreferrer"
        >
          Source
        </a>
      </nav>
    </header>
  );
}
