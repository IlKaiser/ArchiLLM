# SYSTEM DESCRIPTION:

LuckyBets è una piattaforma web che permette agli utenti di partecipare a giochi d’azzardo decentralizzati come Coin Flip, Lottery e Scratch & Win. Tutte le transazioni sono gestite tramite smart contract su blockchain per garantire trasparenza e sicurezza. Il sistema è organizzato in microservizi containerizzati tramite Docker.

# USER STORIES:

1) Come utente, voglio connettere il mio wallet per accedere ai giochi in sicurezza  
2) Come utente, voglio vedere il numero di giocatori online per valutare l’attività della piattaforma  
3) Come utente, voglio selezionare l’importo della scommessa nel Coin Toss  
4) Come utente, voglio scegliere tra testa o croce nel Coin Toss  
5) Come utente, voglio vedere le scommesse attuali degli altri giocatori nel Coin Toss  
6) Come utente, voglio vedere le firme del round per verificare la correttezza  
7) Come utente, voglio scegliere quanti biglietti comprare nella Lottery  
8) Come utente, voglio confermare la transazione nel wallet popup  
9) Come utente, voglio vedere lo storico delle vincite della Lottery  
10) Come utente, voglio ricevere conferma dell’acquisto del biglietto  
11) Come utente, voglio vedere la data della prossima estrazione  
12) Come utente, voglio acquistare una scratchcard  
13) Come utente, voglio grattare la scratchcard con il mouse  
14) Come utente, voglio ricevere feedback immediato sulla vincita  
15) Come utente, voglio acquistare più scratchcard insieme  
16) Come utente, voglio accedere a una sezione di aiuto  
17) Come utente, voglio vedere i jackpot attuali  
18) Come utente, voglio vedere le ultime vincite  
19) Come utente, voglio vedere le statistiche della piattaforma  

# CONTAINERS:

## CONTAINER_NAME: Client

### DESCRIPTION:
Gestisce la UI e l’interazione utente, inclusa la connessione wallet, la visualizzazione dei giochi, delle statistiche e delle vincite. Permette di partecipare a Coin Flip, Lottery e Scratch & Win.

### USER STORIES:
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19

### PORTS:
3000:3000

### PERSISTENCE EVALUATION:
Non richiede database locale, si affida a smart contract e backend per dati persistenti.

### EXTERNAL SERVICES CONNECTIONS:
- Blockchain (Ethereum/compatible)
- Wallet provider (es. MetaMask, WalletConnect)

### MICROSERVICES:

#### MICROSERVICE: client
- TYPE: frontend
- DESCRIPTION: Next.js app che gestisce la UI, la connessione wallet e le chiamate ai servizi backend/smart contract.
- PORTS: 3000
- PAGES:
    | Name         | Description                                 | User Stories |
    |--------------|---------------------------------------------|--------------|
    | /            | Home, statistiche, giochi in evidenza       | 2, 16, 17, 18, 19 |
    | /coinflip    | Coin Flip game                              | 3, 4, 5, 6   |
    | /lottery     | Lottery game                                | 7, 8, 9, 10, 11 |
    | /scratchcard | Scratch & Win game                          | 12, 13, 14, 15 |

---

## CONTAINER_NAME: Server

### DESCRIPTION:
Gestisce la logica backend, la comunicazione P2P per Coin Flip, la gestione dei round, la presenza online e la comunicazione tra utenti.

### USER STORIES:
2, 3, 4, 5, 6

### PORTS:
4005:4005

### PERSISTENCE EVALUATION:
Mantiene in memoria i round attivi e la lista degli utenti online. Non richiede database persistente.

### EXTERNAL SERVICES CONNECTIONS:
- Client (WebSocket)
- Blockchain (per verifica round e payout)

### MICROSERVICES:

#### MICROSERVICE: server-be
- TYPE: backend
- DESCRIPTION: Node.js server che gestisce WebSocket, matchmaking Coin Flip, presenza utenti, gestione round.
- PORTS: 4005

---

## CONTAINER_NAME: Anvil

### DESCRIPTION:
Smart contract per la gestione della Lottery: acquisto biglietti, estrazione vincitori, storico vincite e per la gestione delle scratchcard: acquisto, verifica vincita, payout.

### USER STORIES:
7, 8, 9, 10, 11, 12, 13, 14, 15

### PORTS:
N/A (deploy su blockchain)

### PERSISTENCE EVALUATION:
Tutti i dati sono persistenti su blockchain.

### EXTERNAL SERVICES CONNECTIONS:
- Client (tramite web3)
- Wallet utente

### MICROSERVICES:

#### MICROSERVICE: lottery
- TYPE: smart contract
- DESCRIPTION: Gestisce logica lottery, acquisto biglietti, estrazione, payout.
- TECHNOLOGY: Solidity

---

# NOTE TECNICHE

- Tutti i container sono orchestrati tramite Docker e docker-compose.
- La comunicazione tra frontend e backend avviene tramite WebSocket.
- L’integrazione wallet è realizzata tramite librerie wagmi/connectkit.
- I dati di gioco e le transazioni sono garantiti da smart contract su blockchain.

# DB STRUCTURE

- Non sono previsti database tradizionali: la persistenza è affidata a smart contract e storage temporaneo in memoria per la presenza online e i round attivi.

# PERSISTENCE

- Blockchain per giochi e transazioni
- In-memory per presenza e round Coin Flip

# EXTERNAL SERVICES

- Blockchain node (Ethereum/compatibile)
- Wallet provider
---