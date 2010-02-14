import yaml

import model
import ser

def MakeYamlArray(field, data):
    arr = []
    for i in range(field.typ.GetLength()):
        elt = field.Get(i)
        if isinstance(elt.typ, model.Value):
            val = data.Get(elt.loc)
            arr.append(val)
        elif isinstance(elt.typ, model.Struct):
            val = MakeYamlObject(elt, data)
            arr.append(val)
        else:
            raise RuntimeError(elt.typ)
    return arr

def MakeYamlNamedArray(field, data):
    arr = {}
    for i in range(field.typ.GetLength()):
        elt = field.Get(i)
        if isinstance(elt.typ, model.Value):
            val = data.Get(elt.loc)
            arr[field.typ.GetName(i)] = val
        elif isinstance(elt.typ, model.Struct):
            val = MakeYamlObject(elt, data)
            arr[field.typ.GetName(i)] = val
        else:
            raise RuntimeError(elt.typ)
    return arr

def MakeYamlObject(var, data):
    assert isinstance(var.typ, model.Struct)
    obj = {}
    for name in var.typ.GetNames():
        field = var.Get(name)
        if isinstance(field.typ, model.Value):
            val = data.Get(field.loc)
            obj[name] = val
        elif isinstance(field.typ, model.Array):
            if field.typ.HaveNames():
                obj[name] = MakeYamlNamedArray(field, data)
            else:
                obj[name] = MakeYamlArray(field, data)
        elif isinstance(field.typ, model.Struct):
            val = MakeYamlObject(field, data)
            obj[name] = val
    return obj


def ParseYamlArray(field, data, arr):
    for i in range(field.typ.GetLength()):
        elt = field.Get(i)
        if isinstance(elt.typ, model.Value):
            data.Set(elt.loc, arr[i])
        elif isinstance(elt.typ, model.Struct):
            ParseYamlObject(elt, data, arr[i])
        else:
            raise RuntimeError(elt.typ)

def ParseYamlNamedArray(field, data, obj):
    for i in range(field.typ.GetLength()):
        elt = field.Get(i)
        if isinstance(elt.typ, model.Value):
            data.Set(elt.loc, obj[field.typ.GetName(i)])
        elif isinstance(elt.typ, model.Struct):
            ParseYamlObject(elt, data, obj[field.typ.GetName(i)])
        else:
            raise RuntimeError(elt.typ)

def ParseYamlObject(var, data, obj):
    assert isinstance(var.typ, model.Struct)
    for name in var.typ.GetNames():
        field = var.Get(name)
        if isinstance(field.typ, model.Value):
            data.Set(field.loc, obj[name])
        elif isinstance(field.typ, model.Array):
            if field.typ.HaveNames():
                ParseYamlNamedArray(field, data, obj[name])
            else:
                ParseYamlArray(field, data, obj[name])
        elif isinstance(field.typ, model.Struct):
            ParseYamlObject(field, data, obj[name])

def Save(var, data, fname):
    f = open(fname, "w")
    f.write(yaml.dump(MakeYamlObject(var, data)))
    f.close()

def Load(var, data, fname):
    obj = yaml.load(open(fname))
    ParseYamlObject(var, data, obj)
    return data
