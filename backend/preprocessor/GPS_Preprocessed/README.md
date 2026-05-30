# GPS/location Preprocessing

This ```gps.py``` for now taking input from csv file...

It also lacking some stuffs 

but before that lemme explain you the entities and relation will form after preprocessing.

## Some Helper Functions -
- generate temp_id function $\rightarrow$ need temp_id for each nodes and edges json
- calculate_distance function $\rightarrow$ It basically takes latitude and logitude of two locations, and calculate shortest distance between those points on curve surface of earth.
We are gonna use **harvesine distance** formula to calculate that...
**The Math Behind this...**
If we have points 1 = lat1, long1
and points 2 = lat2, long2
then we will calculate, delta value of latitudes (dlat) = |lat2 - lat1|
and delta value of longitudes (dlong) = |long2 - long1|
$
a = \sin^2\left(\frac{dlat}{2}\right) + \cos(lat1) \cdot \cos(lat2) \cdot \sin^2\left(\frac{dlong}{2}\right)\newline
c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)\newline
d = R \cdot c \rightarrow $ considering R = radius of earth in meters

- normalise_timestamp function $\rightarrow$ basically normalise the timestamp in isoformat

---

## Real preprocessing
1. loads the file (csv, excel, or json)
2. create some storage for computation later on (entities, relations, entity_lookup, previous_locations)
3. Now iterating record one by one row
   - ceating and setting a tracked_entity_id and tracked_entity_type for different types of devices with gps
   - accessing location (latitude, longitude) and then validate it
   - accessing some optional field (like timestamp, accuracy, speed, source)
   - Creating tracked entity node
   - Creating location node
   - Creating LOCATED_AT relation [shows the current location of that device]
   - Creating MOVED_TO relation [shows where it moved from initial position]
   - stores in previous_location storage, so that it can be of help 
   - return the output as entities(nodes) and relations (edges)

---

## Nodes and Edges present
We will have entities(nodes) for 
- tracked entity node
- location node

We will have relations(edges) for 
- LOCATED_AT $\rightarrow$ shows the current location of that device
- MOVED_TO $\rightarrow$ shows where it moved from initial position

It lack stuffs like 
- confidence scores are hard coded