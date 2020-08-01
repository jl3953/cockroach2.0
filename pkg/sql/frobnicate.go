package sql

import (
	"context"
	//"log"
	//"time"

	"github.com/cockroachdb/cockroach/pkg/sql/sem/tree"
	"github.com/cockroachdb/errors"

	//"google.golang.org/grpc"
	//pb "google.golang.org/grpc/examples/helloworld"

)

const (
	address = "localhost:50051"
	defaultName = "world"
)

func (p *planner) Frobnicate(ctx context.Context, stmt *tree.Frobnicate) (planNode, error) {

	// Set up a connection to the server
	/**log.Printf("jenndebug attempt to connect to %v\n", address)
	conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	if err != nil {
		log.Fatalf("jenndebug did not connect: %v", err)
	}
	log.Printf("jenndebug connected to %v\n", address)
	defer conn.Close() **/
	//c := pb.NewGreeterClient(conn)

	// Contact the server and print out its response.
	/**
	name := defaultName
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	**/

	return nil, errors.AssertionFailedf("We're not quite frobnicating yet...")
}
