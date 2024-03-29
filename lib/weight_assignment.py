db_weight = "./lib/weights/"
outdated_HP = "./lib/outdated_HP/"
skewnessfile = './lib/skewness/'


def assign(hp, model='sk', replaced_by = None):

    global error_message

    # start with no error messages when method first called
    if not replaced_by:
        error_message = None

    # Check HP id format should be 'HP_nnnnnnn'
    if(hp[2] == ":"):
        hp = hp.replace(":", "_", 1)
    
    try:
        if( model == 'sk'):
            with open(skewnessfile + hp, "r") as fr:
                data = fr.read().rstrip('\n').split("\t")
            return (float(data[0]), replaced_by, error_message)
        else:
            with open(db_weight + hp, "r") as fr:
                data = fr.read().split("\n")
                if(model == 'ic'):

                    return (float(data[1]), replaced_by, error_message)
                if(model == 'w'):
                    return (float(data[2]), replaced_by, error_message)
            
        return (1.0, replaced_by, error_message)
    except FileNotFoundError:
        try:
            with open(outdated_HP + hp, "r") as fr:
                
                data = fr.read().split("\n")
                
                # this outdated HP is replaced by another HP, so assign it the weight of the new HP.
                if(len(data[1]) >0):
                    error_message = (hp.replace("_",":") +" ("+ data[0] +")" +" is obsolete, and replaced by "+ data[1].replace("_",":") +".\nPhen2Gene gave the weight of "+ data[1].replace("_",":") + " to " + hp.replace("_",":")+" .")
                    var1, var2, var3 = assign(data[1], model, data[1])
                    return (var1, var2, error_message)
                
                # this HPO term is outdated. It have references to other currently valid HPO terms
                if(len(data[2]) >0):
                    error_message = (hp.replace("_",":") +" ("+ data[0] +")" + " is obsolete.\nPhen2Gene skipped it.")
                    refs = data[2].split(",")
                    
                    for ref in refs:
                        error_message += ("Consider: " + ref.replace("_",":"))
                    return (0, None, error_message)
        except FileNotFoundError:
            pass
        error_message = (hp.replace("_", ":",1) + " is not a valid human phenotype.\nPhen2Gene skipped it.")
        return (0, None, error_message) 
