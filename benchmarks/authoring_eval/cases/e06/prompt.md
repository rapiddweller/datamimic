Create a repeatable staffing register of five datasets: `companies`, `people`, `employments`, `licenses` and `assignments`. Use seed `61423`.

`companies` holds exactly 4 companies. Each company has:

- `company_id`, the whole numbers 1, 2, 3 and 4;
- `name`, a generated text that is never empty.

`people` holds exactly 20 people. Each person has:

- `person_id`, the whole numbers 1 to 20;
- `badge`, the text `P-` and then the `person_id` with three digits, for example `P-007` for person 7;
- `full_name`, a generated text that is never empty.

`employments` holds exactly 2 employments for each person, 40 in total. Each employment has:

- `employment_id`, a whole number that is different for every employment;
- `person_id`, the `person_id` of the person;
- `company_id`, the `company_id` of a company in `companies`;
- `function`, drawn from the weighted list in `fixtures/functions.wgt.csv`. Each line of that pipe-separated UTF-8 file holds a function and its weight, and the file has no header row. A weight is the relative share.

A person never has two employments at the same company.

`licenses` holds exactly 2 licenses for each person, 40 in total. Each license has:

- `license_id`, a whole number that is different for every license;
- `person_id`, the `person_id` of the person;
- `valid_from`, a date from 2026-01-01 to 2026-03-31;
- `expires_on`, a date from 2026-03-01 to 2026-12-31, or null when the license has no expiry date.

Exactly 10 of the 40 licenses have no expiry date.

`assignments` holds exactly 5 assignments for each company, 20 in total. Each assignment has:

- `assignment_id`, a whole number that is different for every assignment;
- `person_id`, `company_id` and `function`: the person has an employment at this company in this function;
- `work_date`, a date from 2026-03-01 to 2026-03-31.

On the `work_date`, the person holds a valid license. A license is valid from its `valid_from` day to its `expires_on` day, and both days count. A license without an expiry date is never valid.
A person has at most one assignment on the same `work_date`.

Write every date as a text `YYYY-MM-DD`. Write a missing expiry date as null, not as an empty text. Every range includes both ends.
