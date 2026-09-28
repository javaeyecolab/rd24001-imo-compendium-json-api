# Source notes

## IMO Compendium

- Current baseline used: FAL.5/Circ.56, approved at FAL 50 (23-27 March 2026).
- IMO Compendium current site: https://imocompendium.imo.org/public/IMO-Compendium/Current/in1.htm
- Dataset contents: https://imocompendium.imo.org/public/IMO-Compendium/Current/content.htm

The 12 dataset scope used by this RD24001 package follows the project source material:
General Declaration; Cargo Declaration; Ship's Stores Declaration; Crew's Effects Declaration; Crew List; Passenger List; Dangerous Goods Manifest; Delivery Bill for Mail Consignment; Maritime Declaration of Health; Ship Sanitation Certificate; Security Report; Advance Notification for Waste Delivery.

Verified IMO Data Numbers included in `imoDataReferences` were taken from current/draft Compendium dataset pages where the element was directly visible. Fields without a verified Data Number are intentionally left without invented IMO numbers.

## UN/CEFACT JSON

- JSON Schema Naming and Design Rules v1.0: https://unece.org/trade/trade-facilitation-and-e-businessuncefact/json-schema-naming-and-design-rules

This repository uses an implementation profile inspired by the UN/CEFACT JSON NDR. It is not represented as an official UN/CEFACT or IMO normative schema.

## GitHub Pages

- GitHub Pages can publish static files from `/docs` on a branch.
- GitHub Pages does not run Python server-side applications; therefore this repository exposes read-only JSON GET endpoints as static files.
