from cipher.core import brain, recon_pipeline
from cipher.skills import skill


@skill("recon_report",
       "Run a full recon dossier on a domain: WHOIS, subdomains, open ports, and TLS "
       "certificate, chained into one report. Active parts only run if the domain is "
       "in scope.",
       {"domain": {"type": "string"}}, ["domain"])
def recon_report(domain):
    return recon_pipeline.run(domain, brain.get_mode())
