String.prototype.isCidrV4=function () {
    var re=/^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$/
    return re.test(this)
};

function check_cidr(cidr, max_net_len) {
    if(!cidr.isCidrV4()){
        return false;
    }
    var net_len=cidr.split('/')[1];
    if(net_len>max_net_len){return false;}
    return true
}