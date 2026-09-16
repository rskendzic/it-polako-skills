# Doprinosi

Predlozi i pull requestovi su dobrodošli.

## Pravila

- Podrazumevani javni jezik je srpski, latinica i ekavica.
- Ne dodajte privatne ili stvarne poslovne dokumente u primere i evalove.
- Svako novo ponašanje mora imati sintetički eval sa `must` i `must_not` kriterijumima.
- Provider-specifična logika ne sme da zameni kanonski `SKILL.md`.
- HTML mora ostati samostalan i funkcionalan bez mreže.
- Ne kopirajte kod ili tekst iz srodnih projekata bez kompatibilne licence i jasnog navođenja porekla.

Pre slanja promene pokrenite:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```
