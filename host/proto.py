import model
import model_pb2

def MakeProto(var, data):
    assert isinstance(var.typ, model.Struct)
    protoname = var.typ.GetName()
    protoclass = model_pb2.__dict__[protoname]
    proto = protoclass()
    for name in var.typ.GetNames():
        f = var.Get(name)
        if isinstance(f.typ, model.Value):
            val = data.Get(f.loc)
            setattr(proto, name, val)
        elif isinstance(f.typ, model.Array):
            for i in range(f.typ.GetLength()):
                elt = f.Get(i)
                if isinstance(elt.typ, model.Value):
                    val = data.Get(elt.loc)
                    getattr(proto, name).append(val)
                elif isinstance(elt.typ, model.Struct):
                    structproto = MakeProto(elt, data)
                    p = getattr(proto, name).add()
                    p.CopyFrom(structproto)
                else:
                    raise RuntimeError(elt.typ)
        elif isinstance(f.typ, model.Struct):
            structproto = MakeProto(t, data)
            getattr(proto, name).CopyFrom(structproto)
    return proto

    
def ParseProto(var, data, proto):
    assert isinstance(var.typ, model.Struct)
    for name in var.typ.GetNames():
        f = var.Get(name)
        if isinstance(f.typ, model.Value):
            val = getattr(proto, name)
            data.Set(f.loc, val)
        elif isinstance(f.typ, model.Array):
            assert f.typ.GetLength() == len(getattr(proto, name))
            for i in range(f.typ.GetLength()):
                elt = f.Get(i)
                if isinstance(elt.typ, model.Value):
                    val = getattr(proto, name)[i]
                    data.Set(elt.loc, val)
                elif isinstance(elt.typ, model.Struct):
                    structproto = getattr(proto, name)[i]
                    ParseProto(elt, data, structproto)
                else:
                    raise RuntimeError(elt.typ)
        elif isinstance(f.typ, model.Struct):
            structproto = getattr(proto, name)
            ParseProto(f, data, structproto)
    
