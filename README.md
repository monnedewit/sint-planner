# Sint-planner (FC Berghuizen)

Planning van Sinterklaasroutes: chauffeurs, sinterklazen en pieten per route.

## Database opzetten (Supabase)
1. Maak een gratis project op supabase.com.
2. SQL Editor: voer `db/schema.sql` uit, daarna `db/seed.sql` (importeert de routes uit de Word-lijst).
3. Authentication > Users: maak jezelf aan en voeg je user-id toe aan tabel `planners`.

`data/routes.json` is dezelfde data als leesbaar bestand; `parse.py` zet de Word-lijst om.
