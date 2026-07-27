# FantaBeach bot

Pubblica su Telegram le immagini dei risultati, leggendo `fivb_matches` da Supabase.
Nessun trigger: gira ogni 10 minuti e pubblica solo le partite non ancora in `posted_items`.

## Configurazione (una volta sola)

### 1. Bot Telegram
1. Su Telegram scrivi a `@BotFather` → `/newbot` → ricevi il **token**
2. Crea un canale privato, aggiungi il bot come amministratore
3. Manda un messaggio nel canale, poi apri
   `https://api.telegram.org/bot<TOKEN>/getUpdates` e leggi `chat.id`
   (per i canali e' negativo, tipo `-1001234567890`)

### 2. Secrets su GitHub
Settings → Secrets and variables → Actions → New repository secret:

| Nome | Valore |
|---|---|
| `SUPABASE_URL` | `https://<progetto>.supabase.co` |
| `SUPABASE_ANON_KEY` | chiave **anon**, mai la service_role |
| `TELEGRAM_TOKEN` | token di BotFather |
| `TELEGRAM_CHAT_ID` | id del canale |

### 3. Policy su Supabase
```sql
ALTER TABLE posted_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bot legge"  ON posted_items FOR SELECT TO anon USING (true);
CREATE POLICY "bot scrive" ON posted_items FOR INSERT TO anon WITH CHECK (true);
```

### 4. Template
`templates/<tappa>/QUALIFICATION.png` e gli altri 6, con i nomi esatti:
`QUALIFICATION` `POOL` `ROUND_OF_12` `QUARTERFINAL` `SEMIFINAL` `FINAL_3_4` `FINAL_1_2`
Poi aggiungi i due `vis_id` della tappa a `templates/index.json`.

## Uso

**Prova a vuoto** (genera le immagini, non manda niente):
Actions → Pubblica risultati → Run workflow → tornei `9397,9398`, prova `true`
Le immagini si scaricano dagli artifact.

**Manuale su una tappa**: stesso percorso con prova `false`.

**Automatico**: gira da solo ogni 10 minuti sui tornei con `status='ongoing'`.

## Sicurezza
- Repo pubblico = **log delle Actions pubblici**. Non stampare mai URL completi o header.
- I secret non vengono passati alle pull request da fork.
- I workflow schedulati si disattivano dopo ~60 giorni senza commit sul repo.

## Limiti
- max 15 invii per giro, 4 secondi di pausa: il resto parte al giro dopo
- una fase non riconosciuta non viene pubblicata, arriva un alert su Telegram
