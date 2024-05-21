# Capsim

Capsim è un software per simulare e confrontare investimenti a lungo termine basandosi sui prezzi storici di diversi asset.

Capsim è un'applicazione web con architettura a client-server strettamente separati. `capsim` è il progetto web server, e `capsim-client-ts` rappresenta un'implementazione del web client. Utilizzano technologie e linguaggi di programmazione diversi.

- `capsim` è un web server `Flask` scritto in python che espone una HTTP API JSON REST. Esegue simulazioni finanziarie, e gestisce la banca dati relativa ai prezzi storici degli asset, ottenendo informazioni dalle HTTP API di AlphaVantage e salvandole nel database SQLite.

- `capsim-client-ts` è un web client per `capsim` che presenta un'interfaccia grafica per configurare le simulazioni finanziare e consente di visualizzarle e confrontarle tramite grafici interattivi. `capsim-client-ts` è una web app SPA basata su React, scritta in typescript. Comunica con `capsim` utilizzando la sua interfaccia HTTP.

# Server

Il lato server di capsim è un server python Flask.
Il server utilizza solamente variabili d'ambiente per la sua configurazione.
- `API_KEY` definisce la chiave API per AlphaVantage usata per ottenere gli storici dei prezzi e dati inflazionari
- `ADMIN_PASS` definisce la password amministrativa utilizzata per certe operazioni privilegiate tramite API
- `DB_FILE` definisce il file da utilizzare per il database SQLite.

All'avvio, viene chiamata la procedura `ensure_initialization()` che a sua volta comincia chiamando `load_environment_variables()`.

Quest'ultima legge le chiavi definite nell'opzionale file `.env` e le carica come variabili d'ambiente.

Successivamente, in `ensure_initialization()`, ci assicuriamo che il database esista, che abbia i dati del CPI per l'inflazione e almeno un asset, `VTI`.

## SQLite

In `db.py` troviamo tutte le funzioni che interagiscono con il DB SQLite:

- `fetch_and_save_timeseries(ticker, type)` scarica informazioni su un asset o dati inflazionari da AlphaVantage e li salva nel database.

- `load_timeseries(ticker)` ottiene i prezzi storici di un asset salvati nel nostro database, e li combina con i dati inflazionari del CPI in un dataframe Pandas, che poi restituisce

- `erase_ticker(ticker, type)` elimina tutte le informazioni salvate relative ad un particolare asset

- `list_tickers(type)` restituisce una lista di asset presenti nel database

Tutte queste funzioni vengono poi chiamate dai request handler Flask, definiti in `server.py`

## HTTP Request handler

Tutti gli handler per le richieste HTTP si trovano in `server.py`.
Si tratta di endpoint che richiedono JSON e restituiscono JSON, in maniera stateless, e che usano metodi HTTP come GET, POST, DELETE, PUT a seconda del tipo di operazione, restituendo codici di risposta HTTP adeguati a seconda del caso.

In altre parole si tratta di un'interfaccia HTTP RESTful che utilizza JSON.

Alcuni di questi endpoint espongono azioni privilegiate che necessitano di autorizzazione dell'admin del nostro sistema.

Sono gli endpoint per scaricare un nuovo asset (o aggiornarne uno esistente), eliminare un'asset esistente, e per controllare se si ha accesso privilegiato.

L'autenticazione avviene tramite header Authorization. Semplicemente il client imposta la ADMIN_PASS definita precedentemente nelle variabili d'ambiente come valore dell'Authorization header nelle proprie richieste.

Se le password coincidono, consentiamo l'uso di metodi privilegiati.

Altrimenti, restituiamo il codice HTTP `401, Unathorized`.

### Possibili miglioramenti futuri
Per maggiore sicurezza, invece di tenere la password nelle variabili d'ambiente in plaintext, potremmo usare una funzione di hash sicura per le password, anche aggiungento un salt.

La password passata tramite variabile d'ambiente potrebbe fungere come password iniziale, dopo essersi autenticato la prima volta l'admin ne dovrebbe impostare una permanente tramite interfaccia web, e questa password permanente verrebbe passata nella funzione di hash e il risultato salvato nel database per autenticazione futura.

Successivamente, invece di validare direttamente la password per ogni richiesta, potremmo creare un endpoint per il login che accetta la password e restituisce un JWT firmato digitalmente dal server da usare successivamente negli authorization header per le richieste che richiedo accesso privilegiato.

In ogni caso per ora il livello di sicurezza corrente è sufficiente.

## Simulazione

Per simulare l'andamento di un portfolio basato su un certo asset e i parametri forniti dall'utente, utilizziamo la liberia `Pandas` assieme ad un algoritmo implementato in `strategy.py`

La funzione principale è `process_strategy()` che esegue la simulazione mese per mese in base alle condizioni iniziali e ai dati di prezzi e inflazione.

`annualize()` prende i dati ottenuti dalla simulazione mese per mese, e le annualizza, restituendoci informazioni anno per anno.

`cut_data_and_normalize()` opzionalmente taglia i dati precedenti una certa data in modo da simulare un determinato momento di inizio per i nostri investimenti.

Successivamente, normalizza i prezzi dell'asset in modo che siano sempre `100` all'inizio, e i dati inflazionari in modo che comincino sempre da `1`. Questo semplifica i calcoli successivi.

## Portfolio

`Portfolio` è la classe che agisce come interfaccia per poter utilizzare le simulazioni in modo semplice ed ergonomico. Si trova in `portfolio.py` e gestisce i parametri input oltre a ottenere i dati sorgente tramite le funzioni del database, e svolgere i calcoli usando `Pandas` tramite le funzioni definite in `strategy.py`

Portfolio viene chiamato dall'handler `backtest()` in `server.py`

# Client

Il nostro client è una SPA basata su React scritta in Typescript e JSX, che presenta un'interfaccia grafica con cui utilizzare le funzioni presentate dal server.

L'unica configurazione è una singola variabile d'ambiente,`VITE_REACT_APP_API_URL` che rappresenta l'URL del nostro server API.

L'interazione con la nostra REST API avviene tramite una serie di hook React definiti in `src/hooks` che utilizzano Axios per fare le richieste HTTP, e gestiscono le risposte, esponendo un'interfaccia semplificata al resto dell'applicativo.

L'interfaccia grafica è composta utilizzando componenti UI da [Shadcn/ui](https://ui.shadcn.com/docs/) che si trovano in `src/components/ui`. Non si tratta di una libreria; I componenti sono da copiare ed incollare nel proprio progetto, consentendo una customizzazione senza limiti.

Sia il nostro client che i componenti Shadcn utilizzano TailwindCSS per semplificare la creazione di stili. TailwindCSS ci fornisce molte classi CSS già pre-fatte, evitandoci la creazioni di classi nostre.

Il client ha due route, `/` (Dashboard principale) e `/admin`, l'ultima accessibile solo ai possessori della password.

## Dashboard

La dashboard principale, che troviamo sotto `/`, è il luogo dove un utente può impostare simulazioni d'investimenti.

I parametri di queste simulazioni vengono "salvate" come parametri nella query string. Questo permette, ad esempio, di creare segnalibri nel browser per accedere a simulazioni passate, ma anche la possibilità di condividere delle simulazioni con altri utenti di capsim copiando ed incollando l'indirizzo corrente dalla barra del browser.

## Admin Dashboard

L'Admin Dashboard consente di aggiungere ed aggiornare asset nel database, ed eliminare un asset precedentemente salvato.
Per accedere alla dashboard, è necessario essere in possesso della password impostata nel server, che verrà richiesta. Se la password è corretta, verrà salvata in un cookie in modo da non doverla più inserire manualmente.

La password viene utilizzata come authorization header nelle richieste HTTP di Axios verso il server.
