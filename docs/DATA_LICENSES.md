# Bible Translation Data Licensing

This file documents the licensing status and provenance of the Bible translation XML data used by this application.

## Summary
All translations currently used by this deployment are public domain. This means they may be freely copied, distributed, and used without restriction. The *application source code* remains licensed separately under the MIT License (see `LICENSE`).

If at any point **non–public-domain** or **restricted** translations are added, they MUST be explicitly listed below with their license terms and any attribution or usage restrictions.

## Current Public Domain Translations
| Identifier | Name (Common) | Language | Source / Provenance | Notes |
|-----------|---------------|----------|---------------------|-------|
| web | World English Bible | English | Public domain (modern update of ASV) | No restrictions |
| kjv | King James Version | English | Public domain (UK Crown rights expired) | Widely distributed |
| asv | American Standard Version | English | Public domain | Basis for WEB |
| darby | Darby Translation | English | Public domain | 1890 edition |
| ylt | Young's Literal Translation | English | Public domain | 1898 |
| wbt | Webster's Bible Translation | English | Public domain | 1833 |
| ro-cornilescu | Cornilescu (1924) | Romanian | Public domain (original edition) | Ensure using public domain text |

(Adjust identifiers to match actual blob XML filenames if they differ.)

## Adding a New Translation
Before adding a translation:
1. Verify its license status (public domain, permissive, commercial, restricted).
2. If NOT public domain, add a new row in the "Non–Public Domain Translations" section below.
3. If a license requires attribution or a disclaimer, include verbatim text and (if required) add to `NOTICE`.
4. Avoid embedding proprietary or paid translations (e.g., NIV, ESV) unless you have explicit redistribution rights.

## Non–Public Domain Translations (None Currently)
| Identifier | Name | License | Permitted Use | Attribution Required | Notes |
|-----------|------|---------|---------------|----------------------|-------|
| *(none)* | | | | | |

## File Structure Expectations
Each translation is stored as an XML file in the configured Azure Blob container (default: `bible-translations`). Example naming convention:
```
<identifier>.xml
```
If multiple variants exist (e.g., `web_us.xml`, `web_uk.xml`), document them separately.

## Verification Checklist (When Importing a Translation)
- [ ] License terms reviewed
- [ ] Public domain status confirmed (if claimed)
- [ ] No embedded watermark / DRM markers
- [ ] Encoding normalized (UTF-8)
- [ ] XML validates / parses cleanly
- [ ] Added to this file
- [ ] If not public domain: entry added to NOTICE (if attribution required)

## Disclaimer
This file is provided for documentation convenience and does NOT constitute legal advice. Always confirm license terms from authoritative sources when in doubt.

---
Maintainer: Andrei Demit (2025)
