# MMConnect Scripts

## Load demo data

Run this inside the Odoo.sh shell:

```bash
odoo-bin shell -d p_domusacropoles_teste_29310774 < /home/odoo/src/user/mmconnect/scripts/load_demo_data.py
```

The script is idempotent and will:

- add the current user to `MMConnect Manager`;
- create demo users and employees;
- create reusable data across the main MMConnect menus;
- reuse existing demo records on subsequent executions.
