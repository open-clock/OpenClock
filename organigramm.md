# Team Organization

## Organigramm

```mermaid
stateDiagram-v2 

n : Nicolas Kasper
k : David Klier
b : Benedikt Werner
j : Jan Weichhart

Project : Project Managemet
software : Software Development
Design : Design
Marketing : Marketing
Hardware : Hardware

opencl : Open Clock

opencl --> Project 
opencl --> software 
opencl --> Design
opencl --> Marketing


Project --> b
software --> b 
software --> j
software --> k
Hardware --> j
Hardware --> b
Design --> k
Design --> n
Marketing --> n
Marketing --> k


```
