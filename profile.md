# Your profile

Filled in by `/setup` (or by hand). Every `{{KEY}}` below is a placeholder used across CLAUDE.md, the agents and the
skills. Write your value after the `=` on the same line, then run `python3 scripts/apply_profile.py` to put the values
into every file. The whole system (search, filters, who to contact, what to offer in emails) is built from these.

Each example shows three different jobs (a designer, a developer, a marketer), so you can see the pattern. Write
your own.

## 1. The job you want (start here)

- `{{TARGET_ROLE}}` = 
  The job title you are looking for. Example: Product Designer / Backend Developer / Content Marketer
- `{{ROLE_NOUN}}` = 
  How people say it in one word, used in emails. Example: designer / developer / marketer
- `{{FIELD}}` = 
  Your field in one or two words. Example: design / engineering / marketing
- `{{SENIORITY}}` = 
  Example: Mid-level (2-5 yrs)
- `{{SKILLS}}` = 
  Your main skills and tools. Example: Figma, prototyping / Python, APIs, PostgreSQL / SEO, copywriting, email campaigns
- `{{LOOKALIKE_ROLES}}` = 
  Jobs that share your title words but are a different field, to drop. Example: packaging or furniture design /
  hardware or civil engineering / field sales "marketing" roles
- `{{AMBIGUOUS_TITLES}}` = 
  Titles that are only sometimes your job. Example: "Experience Designer" / "Software Specialist" / "Growth Associate"
- `{{RELEVANT_SIGNALS}}` = 
  What in the posting shows an ambiguous title is really your job. Example: Figma, product, UX / writing code,
  backend services / content, campaigns, analytics
- `{{FIELD_LEADERSHIP_TITLES}}` = 
  Leaders in your field, contacted second after founders. Example: Head of Design, Design Lead / CTO, Head of
  Engineering, Tech Lead / CMO, Head of Marketing, Growth Lead
- `{{HIRING_MANAGER_TITLES}}` = 
  Other people who hire for your role, contacted third. Example: Head of Product, Product Manager / Engineering
  Manager / Head of Growth, Brand Manager

## 2. Where and with whom

- `{{TARGET_MARKETS}}` = 
  The countries you search in. Example: UK and Netherlands
- `{{SPONSOR_DEFAULT_MARKETS}}` = 
  Target markets where employers usually sponsor visas, or "none". Example: none
- `{{COMPANY_SIZE_MAX}}` = 
  Largest company size you want (employees). Example: 50
- `{{COMPANY_TYPES}}` = 
  Example: startups, small studios, agencies
- `{{PAY_FLOOR}}` = 
  Lowest monthly pay that makes a junior role worth it. Example: US$2,000/month
- `{{EXCLUDED_TEAM_BASES}}` = 
  Countries where you do not want the team to be based, or "none". Example: none

## 3. Who you are

- `{{FULL_NAME}}` = 
  Your full name. Every email is signed with it. Example: Jane Doe
- `{{NATIONALITY}}` = 
  Example: Brazilian
- `{{BASE_COUNTRY}}` = 
  The country you live in now. Also used to drop jobs that say people from there are not eligible. Example: Brazil
- `{{LANGUAGES}}` = 
  Languages you work in. Jobs requiring any other language are dropped. Example: English only
- `{{VISA_SITUATION}}` = 
  Example: cannot relocate without visa sponsorship / has EU work rights / remote only

## 4. Your emails

- `{{SIGN_OFF}}` = 
  The word before your name at the end of every email. Example: Hug
- `{{WORK_UNIT}}` = 
  One piece of your work, the thing you offer to do or redo for free. Example: screen / API endpoint / landing page
- `{{FREE_OFFER_EXAMPLES}}` = 
  Small free things you can offer. Example: redo one screen or look at their signup / review one slow endpoint /
  rewrite one landing page or one welcome email
- `{{LINKEDIN_URL}}` = 
  Example: https://www.linkedin.com/in/your-name/
- `{{PORTFOLIO_LABEL}}` = 
  The link text for your work samples. Example: Case studies / GitHub / Writing samples
- `{{PORTFOLIO_URL}}` = 
  Example: https://github.com/your-name
- `{{WEBSITE_URL}}` = 
  Example: https://your-name.com/
