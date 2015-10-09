package main

// Starting at Fri Oct  9 02:15:52 PDT 2015
// Fri Oct  9 03:36:55 PDT 2015 it works
// Fri Oct  9 03:44:42 PDT 2015 finished some tweaks

import (
	"fmt"
	"time"
)

type Router struct {
	id                    int
	currentRootID         int
	currentDistanceToRoot int
	buffer                chan Message // for receiving messages from other routers
	nbrs                  []*Router
}

type Message struct {
	myID           int
	currentRootID  int
	distanceToRoot int
}

func NewRouter(id int) *Router {
	return &Router{id, id, 0, make(chan Message, 1000), make([]*Router, 0)}
}

func (r *Router) PrintState() {
	fmt.Printf("ID: %d   Current Root ID:   %d    Distance to root:   %d\n", r.id, r.currentRootID, r.currentDistanceToRoot)
}

func (r *Router) Send() {
	for _, nbr := range r.nbrs {
		nbr.buffer <- Message{r.id, r.currentRootID, r.currentDistanceToRoot}
	}
}

func (r *Router) Process(msg Message) {
	if msg.currentRootID < r.currentRootID {
		r.currentRootID = msg.currentRootID
		r.currentDistanceToRoot = msg.distanceToRoot + 1
	}
}

func (r *Router) Run() {
	for {
		r.Send()
		r.Process(<-r.buffer)
	}
	// This was almost an opportunity to use "select". Oh well...
}

func main() {
	routers := make([]*Router, 0)
	routers = append(routers, nil)
	for i := 1; i <= 8; i++ {
		routers = append(routers, NewRouter(i))
	}
	routers[1].nbrs = append(routers[1].nbrs, routers[2], routers[7])
	routers[2].nbrs = append(routers[2].nbrs, routers[1], routers[3], routers[4], routers[8])
	routers[3].nbrs = append(routers[3].nbrs, routers[2], routers[4], routers[8])
	routers[4].nbrs = append(routers[4].nbrs, routers[2], routers[3], routers[5], routers[8])
	routers[5].nbrs = append(routers[5].nbrs, routers[4], routers[6], routers[8])
	routers[6].nbrs = append(routers[6].nbrs, routers[5], routers[7], routers[8])
	routers[7].nbrs = append(routers[7].nbrs, routers[1], routers[6], routers[8])
	routers[8].nbrs = append(routers[8].nbrs, routers[2], routers[3], routers[4], routers[5], routers[6], routers[7])

	for i := 1; i <= 8; i++ {
		go routers[i].Run()
	}

	for {
		time.Sleep(1 * time.Second)
		for i := 1; i <= 8; i++ {
			routers[i].PrintState()
		}
		fmt.Println()
	}
}
