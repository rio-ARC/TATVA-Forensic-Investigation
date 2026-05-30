# Call Details Record (CDR) Preprocessing

This ```cdr.py``` for now taking input from csv file...

It also lacking some stuffs 

but before that lemme explain you the entities and relation will form after preprocessing, tho this preprocessing is very much easy...

We will have entities(nodes) for 
- caller number
- reciever number
- Tower Id [through which the numbers will be connected]

We will have relations(edges) for 
- CALLED [phone $\leftrightarrow$ phone]
- CONNECTED_TO_TOWER [phone $\leftrightarrow$ tower]

It lack stuffs like 
- confidence scores are hard coded

