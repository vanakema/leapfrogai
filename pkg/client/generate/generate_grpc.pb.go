// Code generated by protoc-gen-go-grpc. DO NOT EDIT.
// versions:
// - protoc-gen-go-grpc v1.3.0
// - protoc             v3.12.4
// source: generate/generate.proto

package generate

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

const (
	CompletionService_Complete_FullMethodName = "/generate.CompletionService/Complete"
)

// CompletionServiceClient is the client API for CompletionService service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type CompletionServiceClient interface {
	Complete(ctx context.Context, in *CompletionRequest, opts ...grpc.CallOption) (*CompletionResponse, error)
}

type completionServiceClient struct {
	cc grpc.ClientConnInterface
}

func NewCompletionServiceClient(cc grpc.ClientConnInterface) CompletionServiceClient {
	return &completionServiceClient{cc}
}

func (c *completionServiceClient) Complete(ctx context.Context, in *CompletionRequest, opts ...grpc.CallOption) (*CompletionResponse, error) {
	out := new(CompletionResponse)
	err := c.cc.Invoke(ctx, CompletionService_Complete_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// CompletionServiceServer is the server API for CompletionService service.
// All implementations must embed UnimplementedCompletionServiceServer
// for forward compatibility
type CompletionServiceServer interface {
	Complete(context.Context, *CompletionRequest) (*CompletionResponse, error)
	mustEmbedUnimplementedCompletionServiceServer()
}

// UnimplementedCompletionServiceServer must be embedded to have forward compatible implementations.
type UnimplementedCompletionServiceServer struct {
}

func (UnimplementedCompletionServiceServer) Complete(context.Context, *CompletionRequest) (*CompletionResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Complete not implemented")
}
func (UnimplementedCompletionServiceServer) mustEmbedUnimplementedCompletionServiceServer() {}

// UnsafeCompletionServiceServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to CompletionServiceServer will
// result in compilation errors.
type UnsafeCompletionServiceServer interface {
	mustEmbedUnimplementedCompletionServiceServer()
}

func RegisterCompletionServiceServer(s grpc.ServiceRegistrar, srv CompletionServiceServer) {
	s.RegisterService(&CompletionService_ServiceDesc, srv)
}

func _CompletionService_Complete_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(CompletionRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(CompletionServiceServer).Complete(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: CompletionService_Complete_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(CompletionServiceServer).Complete(ctx, req.(*CompletionRequest))
	}
	return interceptor(ctx, in, info, handler)
}

// CompletionService_ServiceDesc is the grpc.ServiceDesc for CompletionService service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var CompletionService_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "generate.CompletionService",
	HandlerType: (*CompletionServiceServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Complete",
			Handler:    _CompletionService_Complete_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "generate/generate.proto",
}