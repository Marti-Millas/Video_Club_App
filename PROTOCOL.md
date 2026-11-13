# Protocol de Comunicació Client/Servidor TCP

Aquest projecte utilitza un protocol personalitzat basat en **JSON sobre TCP** per a la comunicació entre el client i el servidor. L'arquitectura utilitza sockets asíncrons i no bloquejants mitjançant la llibreria AsyncIO de Python.

## 1. Seguretat i Transport (PAC 3)
La comunicació està protegida mitjançant les següents capes de seguretat:
- **Confidencialitat i Autenticació (mTLS):** La connexió està protegida per TLS mitjançant el mòdul `ssl`. El servidor exigeix als clients presentar un certificat X.509 vàlid (signat per una CA interna) per permetre l'establiment de la sessió. El xifratge simètric es negocia automàticament sota el túnel TLS.
- **Integritat (SHA-256):** Es verifica la integritat de cada transmissió. Totes les peticions i respostes s'empaqueten en dues parts:
  1. **Encapçalament (Header):** Un objecte JSON seguit d'un salt de línia (`\n`) amb el format: `{"length": <mida_del_cos>, "sha256": "<hash_sha256>"}\n`
  2. **Cos (Body):** El missatge JSON en si. El receptor en llegeix exactament la quantitat de bytes especificada i en valida el hash abans de processar-lo. Si no coincideix, es descarta la petició.

## 2. Estructura de la Petició (Request)
El cos de la petició s'envia en format JSON codificat en `utf-8`. L'estructura estàndard conté el nom de l'acció i un diccionari amb les dades necessàries:

```json
{
  "action": "nom_de_l_operacio",
  "data": {
    "parametre1": "valor1"
  }
}
```

## 3. Estructura de la Resposta (Response)
El servidor retorna sempre com a cos un JSON codificat en `utf-8` amb el resultat de l'operació. Aquesta resposta inclou l'estat, un missatge descriptiu i les dades sol·licitades (traduïdes a DTOs per aïllar la base de dades):

```json
{
  "status": "success | error",
  "message": "Missatge de confirmació o descripció de l'error",
  "data": [ ... ] 
}
```

## 4. Operacions Suportades (CRUD)
L'enrutador del servidor (`router.py`) suporta les següents accions:

1. **`ping`**: Comprovació bàsica de connexió (Echo). Retorna el mateix missatge enviat.
2. **`create_platform`**: Crea una nova plataforma. 
   - *Requereix*: `name` a dins de `data`.
3. **`list_platforms`**: Llista totes les plataformes.
4. **`delete_platform`**: Esborra una plataforma.
   - *Requereix*: `platform_id` a dins de `data`.
5. **`create_game`**: Crea un nou joc associat a una plataforma. 
   - *Requereix*: `title`, `price` i `platform_id`.
6. **`list_games`**: Retorna la llista completa de jocs guardats a la base de dades.
7. **`delete_game`**: Esborra un joc existent. 
   - *Requereix*: `game_id`.

## 5. Gestió d'Errors
- Si el servidor rep una cadena que no és un JSON vàlid, retorna un error de format.
- Si l'acció sol·licitada no existeix, es retorna un error amb el missatge "Acció no implementada".
- Els errors interns de la base de dades es capturen mitjançant blocs `try/except` per evitar que el servidor caigui, i es retorna el detall a l'atribut `message` amb un `status: "error"`.
- **Errors de Seguretat:** Si un client intenta connectar-se sense un certificat mTLS vàlid o el hash SHA-256 del missatge no coincideix amb l'encapçalament, el servidor tanca la connexió immediatament.