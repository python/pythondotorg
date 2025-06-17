{% load humanize %}
---
title: SPONSORSHIP AGREEMENT{% if renewal %} RENEWAL{% endif %}
geometry:
- margin=1.25in
font-size: 12pt
pagestyle: empty
header-includes:
- \pagenumbering{gobble}
---

**THIS SPONSORSHIP AGREEMENT{% if renewal %} RENEWAL{% endif %}** (the **"Agreement"**)
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

**WHEREAS**, Sponsor {% if renewal %}
and the PSF previously entered into a Sponsorship Agreement
with the effective date of the
{{ previous_effective|date:"j" }}{{ previous_effective_english_suffix }} of {{ previous_effective|date:"F Y" }}
and a term of one year (the “Sponsorship Agreement”).

**WHEREAS**, Sponsor wishes to renew its support of the Programs by making a contribution to the PSF.
{% else %}
wishes to support the Programs by making a contribution to the PSF.
{% endif %}

## AGREEMENT

**NOW, THEREFORE**, in consideration of the foregoing and the mutual covenants contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the Parties hereto agree as follows: 

{% if renewal %}
1. [**Replacement of the Exhibit**]{.underline} Exhibit A to the Sponsorship Agreement is replaced with Exhibit A below.

1. [**Renewal**]{.underline} Approval and incorporation of this new exhibit with the previous Sponsor Benefits shall be considered written notice by Sponsor to the PSF that you wish to continue the terms of the Sponsorship Agreement for an additional year and to contribute the new Sponsorship Payment specified in Exhibit A, beginning on the Effective Date, as contemplated by Section 6 of the Sponsorship Agreement.
{% else %}
1. [**Recitals Incorporated**]{.underline}. Each of the above Recitals is incorporated into and is made a part of this Agreement.

1. [**Exhibits Incorporated by Reference**]{.underline}. All exhibits referenced in this Agreement are incorporated herein as integral parts of this Agreement and shall be considered reiterated herein as fully as if such provisions had been set forth verbatim in this Agreement.

1. [**Sponsorship Payment**]{.underline}. In consideration for the right to sponsor the PSF and its Programs, and to be acknowledged by the PSF as a sponsor in the manner described herein, Sponsor shall make a contribution to the PSF (the "Sponsorship Payment") in the amount shown in Exhibit A. 

1. [**Acknowledgement of Sponsor**]{.underline}. In return for the Sponsorship Payment, Sponsor will be entitled to receive the sponsorship package described in Exhibit A attached hereto (the "Sponsor Benefits").

1. [**Intellectual Property**]{.underline}. The PSF is the sole owner of all right, title, and interest to all the PSF information, including the PSF’s logo, trademarks, trade names, and copyrighted information, unless otherwise provided.

    (a) [Grant of License by the PSF]{.underline}. The PSF hereby grants to Sponsor a limited, non- exclusive license to use certain of the PSF’s intellectual property, including the PSF’s name, acronym, and logo (collectively, the "PSF Intellectual Property"), solely in connection with promotion of Sponsor’s sponsorship of the Programs. Sponsor agrees that it shall not use the PSF’s Property in a manner that states or implies that the PSF endorses Sponsor (or Sponsor’s products or services). The PSF retains the right, in its sole and absolute discretion, to review and approve in advance all uses of the PSF Intellectual Property, which approval shall not be unreasonably withheld.

    (a) [Grant of License by Sponsor]{.underline}. Sponsor hereby grants to the PSF a limited, non-exclusive license to use certain of Sponsor’s intellectual property, including names, trademarks, and copyrights (collectively, "Sponsor Intellectual Property"), solely to identify Sponsor as a sponsor of the Programs and the PSF. Sponsor retains the right to review and approve in advance all uses of the Sponsor Intellectual Property, which approval shall not be unreasonably withheld.

1. [**Term**]{.underline}. The Term of this Agreement will begin on the Effective Date and continue for a period of one (1) year. The Agreement may be renewed for one (1) year by written notice from Sponsor to the PSF.

1. [**Termination**]{.underline}. The Agreement may be terminated (i) by either Party for any reason upon sixty (60) days prior written notice to the other Party; (ii) if one Party notifies the other Party that the other Party is in material breach of its obligations under this Agreement and such breach (if curable) is not cured with fifteen (15) days of such notice; (iii) if both Parties agree to terminate by mutual written consent; or (iv) if any of Sponsor information is found or is reasonably alleged to violate the rights of a third party. The PSF shall also have the unilateral right to terminate this Agreement at any time if it reasonably determines that it would be detrimental to the reputation and goodwill of the PSF or the Programs to continue to accept or use funds from Sponsor. Upon expiration or termination, no further use may be made by either Party of the other’s name, marks, logo or other intellectual property without the express prior written authorization of the other Party.

1. [**Code of Conduct**]{.underline}. Sponsor and all of its representatives shall conduct themselves at all times in accordance with the Python Software Foundation Code of Conduct (https://www.python.org/psf/conduct) and/or the PyCon Code of Conduct (https://pycon.us/code-of-conduct), as applicable. The PSF reserves the right to eject from any event any Sponsor or representative violating those standards.

1. [**Deadlines**]{.underline}. Company logos, descriptions, banners, advertising pages, tote bag inserts and similar items and information must be provided by the applicable deadlines for inclusion in the promotional materials for the PSF.

1. [**Assignment of Space**]{.underline}. If the Sponsor Benefits in Exhibit A include a booth or other display space, the PSF shall assign display space to Sponsor for the period of the display. Location assignments will be on a first-come, first-served basis and will be made solely at the discretion of the PSF. Failure to use a reserved space will result in penalties (up to 50% of your Sponsorship Payment).

1. [**Job Postings**]{.underline}. Sponsor will ensure that any job postings to be published by the PSF on Sponsor’s behalf comply with all applicable municipal, state, provincial, and federal laws.

1. [**Representations and Warranties**]{.underline}. Each Party represents and warrants for the benefit of the other Party that it has the legal authority to enter into this Agreement and is able to comply with the terms herein. Sponsor represents and warrants for the benefit of the PSF that it has full right and title to the Sponsor Intellectual Property to be provided under this Agreement and is not under any obligation to any party that restricts the Sponsor Intellectual Property or would prevent Sponsor’s performance under this Agreement.

1. [**Successors and Assigns**]{.underline}. This Agreement and all the terms and provisions hereof shall be binding upon and inure to the benefit of the Parties and their respective legal representatives, heirs, successors, and/or assigns. The transfer, or any attempted assignment or transfer, of all or any portion of this Agreement by a Party without the prior written consent of the other Party shall be null and void and of no effect.

1. [**No Third-Party Beneficiaries**]{.underline}. This Agreement is not intended to benefit and shall not be construed to confer upon any person, other than the Parties, any rights, remedies, or other benefits, including but not limited to third-party beneficiary rights.

1. [**Severability**]{.underline}. If any one or more of the provisions of this Agreement shall be held to be invalid, illegal, or unenforceable, the validity, legality, or enforceability of the remaining provisions of this Agreement shall not be affected thereby. To the extent permitted by applicable law, each Party waives any provision of law which renders any provision of this Agreement invalid, illegal, or unenforceable in any respect.  

1. [**Confidential Information**]{.underline}. As used herein, "Confidential Information" means all confidential information disclosed by a Party ("Disclosing Party") to the other Party ("Receiving Party"), whether orally or in writing, that is designated as confidential or that reasonably should be understood to be confidential given the nature of the information. Each Party agrees: (a) to observe complete confidentiality with respect to the Confidential Information of the Disclosing Party; (b) not to disclose, or permit any third party or entity access to disclose, the Confidential Information (or any portion thereof) of the Disclosing Party without prior written permission of Disclosing Party; and (c) to ensure that any employees, or any third parties who receive access to the Confidential Information, are advised of the confidential and proprietary nature thereof and are prohibited from disclosing the Confidential Information and using the Confidential Information other than for the benefit of the Receiving Party in accordance with this Agreement. Without limiting the foregoing, each Party shall use the same degree of care that it uses to protect the confidentiality of its own confidential information of like kind, but in no event less than reasonable care. Neither Party shall have any liability with respect to Confidential Information to the extent such information: (w) is or becomes publicly available (other than through a breach of this Agreement); (x) is or becomes available to the Receiving Party on a non-confidential basis, provided that the source of such information was not known by the Receiving Party (after such inquiry as would be reasonable in the circumstances) to be the subject of a confidentiality agreement or other legal or contractual obligation of confidentiality with respect to such information; (y) is developed by the Receiving Party independently and without reference to information provided by the Disclosing Party; or (z) is required to be disclosed by law or court order, provided the Receiving Party gives the Disclosing Party prior notice of such compelled disclosure (to the extent legally permitted) and reasonable assistance, at the Disclosing Party’s cost.

1. [**Independent Contractors**]{.underline}. Nothing contained herein shall constitute or be construed as the creation of any partnership, agency, or joint venture relationship between the Parties. Neither of the Parties shall have the right to obligate or bind the other Party in any manner whatsoever, and nothing herein contained shall give or is intended to give any rights of any kind to any third party. The relationship of the Parties shall be as independent contractors.

1. [**Indemnification**]{.underline}. Sponsor agrees to indemnify and hold harmless the PSF, its officers, directors, employees, and agents, for any and all claims, losses, damages, liabilities, judgments, or settlements, including reasonable attorneys’ fees, costs (including costs associated with any official investigations or inquiries) and other expenses, incurred on account of Sponsor’s acts or omissions in connection with the performance of this Agreement or breach of this Agreement or with respect to the manufacture, marketing, sale, or dissemination of any of Sponsor’s products or services. The PSF shall have no liability to Sponsor with respect to its participation in this Agreement or receipt of the Sponsorship Payment, except for intentional or willful acts of the PSF or its employees or agents. The rights and responsibilities established in this section shall survive indefinitely beyond the term of this Agreement.

1. [**Notices**]{.underline}. All notices or other communications to be given or delivered under the provisions of this Agreement shall be in writing and shall be mailed by certified or registered mail, return receipt requested, or given or delivered by reputable courier, facsimile, or electronic mail to the Party to receive notice at the following addresses or at such other address as any Party may by notice direct in accordance with this Section:


    If to Sponsor:  
    
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {{sponsor.primary_contact.name}}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {{sponsor.name}}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {{sponsor.mailing_address_line_1}}{%if sponsor.mailing_address_line_2%}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {{sponsor.mailing_address_line_2 }}{% endif %}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {{sponsor.city}}, {{sponsor.state}} {{sponsor.postal_code}} {{sponsor.country}}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Facsimile: {{sponsor.primary_contact.phone}}  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: {{sponsor.primary_contact.email}}  

    &nbsp;

    If to the PSF:
    
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Deb Nicholson  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Executive Director  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Python Software Foundation  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 9450 SW Gemini Dr. ECM # 90772  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Beaverton, OR 97008 USA  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Facsimile: +1 (858) 712-8966  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: deb@python.org  

    &nbsp;

    With a copy to:
    
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Archer & Greiner, P.C.  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Attention: Noel Fleming  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Three Logan Square  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1717 Arch Street, Suite 3500  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Philadelphia, PA 19103 USA  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Facsimile: (215) 963-9999  
    > &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: nfleming@archerlaw.com  

    &nbsp;

    Notices given by registered or certified mail shall be deemed as given on the delivery date shown on the return receipt, and notices given in any other manner shall be deemed as given when received.

1. [**Governing Law; Jurisdiction**]{.underline}. This Agreement shall be construed in accordance with the laws of the State of Delaware, without regard to its conflicts of law principles. Jurisdiction and venue for litigation of any dispute, controversy, or claim arising out of or in connection with this Agreement shall be only in a United States federal court in Delaware or a Delaware state court having subject matter jurisdiction. Each of the Parties hereto hereby expressly submits to the personal jurisdiction of the foregoing courts located in Delaware and hereby waives any objection or defense based on personal jurisdiction or venue that might otherwise be asserted to proceedings in such courts.

1. [**Force Majeure**]{.underline}. The PSF shall not be liable for any failure or delay in performing its obligations hereunder if such failure or delay is due in whole or in part to any cause beyond its reasonable control or the reasonable  control of its contractors, agents, or suppliers, including, but not limited to, strikes, or other labor disturbances, acts of God, acts of war or terror, floods, sabotage, fire, natural, or other disasters, including pandemics. To the extent the PSF is unable to substantially perform hereunder due to any cause beyond its control as contemplated herein, it may terminate this Agreement as it may decide in its sole discretion. To the extent the PSF so terminates the Agreement, Sponsor releases the PSF and waives any claims for damages or compensation on account of such termination.

1. [**No Waiver**]{.underline}. A waiver of any breach of any provision of this Agreement shall not be deemed a waiver of any repetition of such breach or in any manner affect any other terms of this Agreement.

1. [**Limitation of Damages**]{.underline}. Except as otherwise provided herein, neither Party shall be liable to the other for any consequential, incidental, or punitive damages for any claims arising directly or indirectly out of this Agreement.

1. [**Cumulative Remedies**]{.underline}. All rights and remedies provided in this Agreement are cumulative and not exclusive, and the exercise by either Party of any right or remedy does not preclude the exercise of any other rights or remedies that may now or subsequently be available at law, in equity, by statute, in any other agreement between the Parties, or otherwise.

1. [**Captions**]{.underline}. The captions and headings are included herein for convenience and do not constitute a part of this Agreement.

1. [**Amendments**]{.underline}. No addition to or change in the terms of this Agreement will be binding on any Party unless set forth in writing and executed by both Parties.

1. [**Counterparts**]{.underline}. This Agreement may be executed in one or more counterparts, each of which shall be deemed an original and all of which shall be taken together and deemed to be one instrument. A signed copy of this Agreement delivered by facsimile, electronic mail, or other means of electronic transmission shall be deemed to have the same legal effect as delivery of an original signed copy of this Agreement.

1. [**Entire Agreement**]{.underline}. This Agreement (including the Exhibits) sets forth the entire agreement of the Parties and supersedes all prior oral or written agreements or understandings between the Parties as to the subject matter of this Agreement. Except as otherwise expressly provided herein, neither Party is relying upon any warranties, representations, assurances, or inducements of the other Party.

{% endif %}
&nbsp;  
  

### \[Signature Page Follows\]

::: {.page-break}
\newpage
:::

## SPONSORSHIP AGREEMENT{% if renewal %} RENEWAL{% endif %}

**IN WITNESS WHEREOF**, the Parties hereto have duly executed this **Sponsorship Agreement{% if renewal %} Renewal{% endif %}** as of the **Effective Date**.

&nbsp;

>    **PSF**:  
>    **PYTHON SOFTWARE FOUNDATION**,  
>    a Delaware non profit corporation

&nbsp;

>    By:        ________________________________  
>    Name:   Loren Crary  
>    Title:     Director of Resource Development

&nbsp;  

&nbsp;

>    **SPONSOR**:  
>    **{{sponsor.name|upper}}**,  
>    a {{sponsor.state}} entity

&nbsp;

>    By:        ________________________________  
>    Name:   ________________________________  
>    Title:     ________________________________

::: {.page-break}
\newpage
:::

## SPONSORSHIP AGREEMENT{% if renewal %} RENEWAL{% endif %}

### EXHIBIT A

1. [**Sponsorship**]{.underline}. During the Term of this Agreement, in return for the Sponsorship Payment, the PSF agrees to identify and acknowledge Sponsor as a {{sponsorship.year}} {{sponsorship.level_name}} Sponsor of the Programs and of the PSF, in accordance with the United States Internal Revenue Service guidance applicable to qualified sponsorship payments.

   Acknowledgments of appreciation for the Sponsorship Payment may identify and briefly describe Sponsor and its products or product lines in neutral terms and may include Sponsor’s name, logo, well-established slogan, locations, telephone numbers, or website addresses, but such acknowledgments shall not include (a) comparative or qualitative descriptions of Sponsor’s products, services, or facilities; (b) price information or other indications of savings or value associated with Sponsor’s products or services; (c) a call to action; (d) an endorsement; or (e) an inducement to buy, sell, or use Sponsor’s products or services. Any such acknowledgments will be created, or subject to prior review and approval, by the PSF.

    The PSF’s acknowledgment may include the following:

    (a) [**Display of Logo**]{.underline}. The PSF will display Sponsor’s logo and other agreed-upon identifying information on www.python.org, and on any marketing and promotional media made by the PSF in connection with the Programs, solely for the purpose of acknowledging Sponsor as a sponsor of the Programs in a manner (placement, form, content, etc.) reasonably determined by the PSF in its sole discretion. Sponsor agrees to provide all the necessary content and materials for use in connection with such display.

    (a) Additional acknowledgment as provided in Sponsor Benefits.

1. [**Sponsorship Payment**]{.underline}. The amount of Sponsorship Payment shall be {{sponsorship.verbose_sponsorship_fee|title}} USD (${{sponsorship.sponsorship_fee|intcomma}}). The Sponsorship Payment is due within thirty (30) days of the Effective Date. To the extent that any portion of a payment under this section would not (if made as a Separate payment) be deemed a qualified sponsorship payment under IRC § 513(i), such portion shall be deemed and treated as separate from the qualified sponsorship payment.

1. [**Receipt of Payment**]{.underline}. Sponsor must submit full payment in order to secure Sponsor Benefits.

1. [**Refunds**]{.underline}. The PSF does not offer refunds for sponsorships. The PSF may cancel the event(s) or any part thereof. In that event, the PSF shall determine and refund to Sponsor the proportionate share of the balance of the aggregate Sponsorship fees applicable to event(s) received which remain after deducting all expenses incurred by the PSF.

1. [**Sponsor Benefits**]{.underline}. Sponsor Benefits per the Agreement are:

    1. Acknowledgement as described under "Sponsorship" above.

{%for benefit in benefits%}    1. {{benefit}}
{%endfor%}

{%if legal_clauses%}1. Legal Clauses. Related legal clauses are:

{%for clause in legal_clauses%}    1. {{clause}}
{%endfor%}{%endif%}
