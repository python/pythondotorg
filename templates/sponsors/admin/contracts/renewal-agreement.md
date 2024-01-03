---
title: SPONSORSHIP AGREEMENT RENEWAL
geometry:
- margin=1.25in
font-size: 12pt
pagestyle: empty
header-includes:
- \pagenumbering{gobble}
---

**THIS SPONSORSHIP AGREEMENT RENEWAL** (the **"Agreement"**)
is entered into and made effective as of the
{{start_date|date:"j"}}{{start_day_english_suffix}} of {{start_date|date:"F Y"}}
(the **"Effective Date"**),
by and between the **Python Software Foundation** (the **"PSF"**),
a Delaware nonprofit corporation,
and **{{sponsor.name|upper}}** (**"Sponsor"**),
a {{sponsor.state}} corporation.
Each of the PSF and Sponsor are hereinafter sometimes individually
referred to as a **"Party"** and collectively as the **"Parties"**.

## RECITALS

**WHEREAS**, the PSF is a tax-exempt charitable organization (EIN 04-3594598)
whose mission is to promote, protect, and advance the Python programming language,
and to support and facilitate the growth of a diverse
and international community of Python programmers (the **"Programs"**);

**WHEREAS**, Sponsor is {{contract.sponsor_info}}; and

**WHEREAS**, Sponsor and the PSF previously entered into a Sponsorship Agreement
with the effective date of the
{{ previous_effective|date:"j" }}{{ previous_effective_english_suffix }} of {{ previous_effective|date:"F Y" }}
and a term of one year (the “Sponsorship Agreement”).

**WHEREAS**, Sponsor wishes to renew its support the Programs by making a contribution to the PSF.

## AGREEMENT

**NOW, THEREFORE**, in consideration of the foregoing and the mutual covenants contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the Parties hereto agree to extend and amend the Sponsorship Agreement as follows:

1. [**Replacement of the Exhibit**]{.underline} Exhibit A to the Sponsorship Agreement is replaced with Exhibit A below.

1. [**Renewal**]{.underline} Approval and incorporation of this new exhibit with the previous Sponsor Benefits shall be considered written notice by Sponsor to the PSF that you wish to continue the terms of the Sponsorship Agreement for an additional year and to contribute the new Sponsorship Payment specified in Exhibit A, beginning on the Effective Date, as contemplated by Section 6 of the Sponsorship Agreement.

&nbsp;  
  

### \[Signature Page Follows\]

::: {.page-break}
\newpage
:::

## SPONSORSHIP AGREEMENT RENEWAL

**IN WITNESS WHEREOF**, the Parties hereto have duly executed this **Sponsorship Agreement Renewal** as of the **Effective Date**.

&nbsp;

**PSF**:  
**PYTHON SOFTWARE FOUNDATION**,  
a Delaware non profit corporation

&nbsp;

By:        ________________________________  
Name:   Loren Crary  
Title:     Director of Resource Development

&nbsp;  

&nbsp;

**SPONSOR**:  
**{{sponsor.name|upper}}**,  
a {{sponsor.state}} entity

&nbsp;

By:        ________________________________  
Name:   ________________________________  
Title:     ________________________________

::: {.page-break}
\newpage
:::

## SPONSORSHIP AGREEMENT RENEWAL

### EXHIBIT A

1. [**Sponsorship**]{.underline} During the Term of this Agreement, in return for the Sponsorship Payment, the PSF agrees to identify and acknowledge Sponsor as a {{sponsorship.year}} {{sponsorship.level_name}} Sponsor of the Programs and of the PSF, in accordance with the United States Internal Revenue Service guidance applicable to qualified sponsorship payments.

   Acknowledgments of appreciation for the Sponsorship Payment may identify and briefly describe Sponsor and its products or product lines in neutral terms and may include Sponsor’s name, logo, well-established slogan, locations, telephone numbers, or website addresses, but such acknowledgments shall not include (a) comparative or qualitative descriptions of Sponsor’s products, services, or facilities; (b) price information or other indications of savings or value associated with Sponsor’s products or services; (c) a call to action; (d) an endorsement; or (e) an inducement to buy, sell, or use Sponsor’s products or services. Any such acknowledgments will be created, or subject to prior review and approval, by the PSF.

    The PSF’s acknowledgment may include the following:

    - [**Display of Logo**]{.underline} The PSF will display Sponsor’s logo and other agreed-upon identifying information on www.python.org, and on any marketing and promotional media made by the PSF in connection with the Programs, solely for the purpose of acknowledging Sponsor as a sponsor of the Programs in a manner (placement, form, content, etc.) reasonably determined by the PSF in its sole discretion. Sponsor agrees to provide all the necessary content and materials for use in connection with such display.

    - Additional acknowledgment as provided in Sponsor Benefits.

1. [**Sponsorship Payment**]{.underline} The amount of Sponsorship Payment shall be {{sponsorship.verbose_sponsorship_fee|title}} USD ($ {{sponsorship.sponsorship_fee}}). The Sponsorship Payment is due within thirty (30) days of the Effective Date. To the extent that any portion of a payment under this section would not (if made as a Separate payment) be deemed a qualified sponsorship payment under IRC § 513(i), such portion shall be deemed and treated as separate from the qualified sponsorship payment.

1. [**Receipt of Payment**]{.underline} Sponsor must submit full payment in order to secure Sponsor Benefits.

1. [**Refunds**]{.underline} The PSF does not offer refunds for sponsorships. The PSF may cancel the event(s) or any part thereof. In that event, the PSF shall determine and refund to Sponsor the proportionate share of the balance of the aggregate Sponsorship fees applicable to event(s) received which remain after deducting all expenses incurred by the PSF.

1. [**Sponsor Benefits**]{.underline} Sponsor Benefits per the Agreement are:

    1. Acknowledgement as described under "Sponsorship" above.

{%for benefit in benefits%}    1. {{benefit}}
{%endfor%}

{%if legal_clauses%}1. Legal Clauses. Related legal clauses are:

{%for clause in legal_clauses%}    1. {{clause}}
{%endfor%}{%endif%}
