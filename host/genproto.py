import model

def WriteProtobufHeader(f):
    f.write("package tx;\n\n")

def ProtoTypeName(typ):
    if isinstance(typ, model.Value):
        return "int32"
    if isinstance(typ, model.Struct):
        return typ.GetName()
    if isinstance(typ, model.Array):
        return ProtoTypeName(typ.GetType())

def WriteStructProtobuf(f, typ):
    for name in typ.GetNames():
        t = typ.GetType(name)
        if isinstance(t, model.Struct):
            WriteStructProtobuf(f, t)
        if isinstance(t, model.Array):
            elt = t.GetType()
            if isinstance(elt, model.Struct):
                WriteStructProtobuf(f, elt)
    f.write("message %s {\n" % typ.GetName())
    for i, name in enumerate(typ.GetNames()):
        t = typ.GetType(name)
        if isinstance(t, model.Value) or isinstance(t, model.Struct):
            f.write("  required %s %s = %s;\n" % (
                ProtoTypeName(t), name, i + 1))
        elif isinstance(t, model.Array):
            f.write("  repeated %s %s = %s;\n" % (
                ProtoTypeName(t), name, i + 1))
    f.write("}\n\n");

def WriteProtobufSpec(f, typ):
    WriteProtobufHeader(f)
    WriteStructProtobuf(f, typ)

def DumpProto():
    f = open("model.proto", "w")
    WriteProtobufSpec(f, model.Model)
    f.close()

DumpProto()
