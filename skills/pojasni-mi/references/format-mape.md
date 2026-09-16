# Format Mape razumevanja

Renderer prima UTF-8 JSON objekat.

## Obavezna polja

```json
{
  "meta": {
    "title": "Naslov",
    "artifact_type": "document",
    "goal": "Šta korisnik mora da razume ili uradi"
  },
  "sections": [
    {
      "id": "stabilan-id",
      "title": "Naziv dela",
      "summary": "Tumačenje običnim jezikom",
      "why_it_matters": "Operativna posledica",
      "source_refs": [
        {
          "label": "Član 4",
          "location": "strana 2",
          "quote": "Kratak izvorni isečak"
        }
      ],
      "details": ["Dodatni kontekst za Idi u detalje"],
      "consequences": ["Praktična posledica"],
      "uncertainties": ["Šta izvor ne razrešava"]
    }
  ],
  "relationships": [],
  "what_if": [],
  "quiz": [],
  "open_questions": []
}
```

Dozvoljeni `artifact_type`: `contract`, `spreadsheet`, `code`, `document`, `diagram`, `url`, `other`.

## What-if vrste

Diskretan scenario:

```json
{
  "id": "kasnjenje",
  "kind": "choice",
  "title": "Kašnjenje",
  "prompt": "Šta ako rok bude propušten?",
  "choices": [
    {
      "label": "3 dana",
      "outcome": "Posledica vezana za izvor",
      "source_refs": ["Član 4"]
    },
    {
      "label": "8 dana",
      "outcome": "Druga posledica vezana za isti izvor",
      "source_refs": ["Član 4"]
    }
  ]
}
```

Proverena linearna relacija:

```json
{
  "id": "cena",
  "kind": "number",
  "title": "Promena količine",
  "prompt": "Izaberi količinu",
  "min": 1,
  "max": 10,
  "step": 1,
  "base_value": 3,
  "unit": "kom",
  "result_unit": "RSD",
  "factor": 1200,
  "offset": 0,
  "precision": 0,
  "source_refs": ["Tabela C2:C11"]
}
```

Renderer ne prihvata proizvoljne izraze i nikada ne koristi `eval`.
Svi brojevi moraju biti konačni, a apsolutna vrednost ne sme preći JavaScript
`Number.MAX_SAFE_INTEGER`; boolean nije broj. `precision`, kada postoji, mora
biti ceo broj od 0 do 20. Slider `step` mora odgovarati floating-point
rezoluciji opsega i opseg ne sme imati više od 1.000.000 koraka. Renderer
proverava i rezultate formule na minimalnoj, maksimalnoj i početnoj vrednosti.

## Kviz

```json
{
  "id": "q1",
  "question": "Primenjeno pitanje",
  "options": ["A", "B", "C"],
  "correct_index": 1,
  "explanation": "Zašto i gde to piše",
  "source_refs": ["Član 4"]
}
```

Svako pitanje mora imati tačno jedan proverljiv odgovor. Ako izvor ne razrešava odgovor, pretvori ga u otvoreno pitanje, ne u kviz.
Svaka vrednost u `source_refs` mora tačno odgovarati `label` vrednosti iz neke
sekcije. Isto pravilo važi za odnose i oba what-if režima.
