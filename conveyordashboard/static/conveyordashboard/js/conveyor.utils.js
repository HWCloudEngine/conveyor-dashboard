/**
 * Copyright 2017 Huawei, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

"use strict";

String.prototype.isCidrV4=function () {
    var re=/^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$/;
    return re.test(this)
};

var conveyorUtil = {
    merge: function (dict1, dict2) {
        $.each(dict2, function (k, v) {
            dict1[k] = v
        });
    },
    checkCidr: function (cidr, max_net_len) {
        if(!cidr.isCidrV4()) {
            return false;
        }
        var net_len=cidr.split('/')[1];
        return net_len <= max_net_len;
    },
    compareIp: function(ipBegin, ipEnd) {
        var temp1 = ipBegin.split("."), temp2 = ipEnd.split(".");
        for (i = 0; i < 4; i++){
            var j = parseInt(temp1[i]), k = parseInt(temp2[i]);
            if (j > k){
                return 1;
            } else if (j < k) {
                return -1;
            }
        }
        return 0;
    },
    ipCheckInCidr: function (pool, ip) {
        try {
            for(var index in pool) {
                if(this.compareIp(pool[index].start, ip) <= 0 && this.compareIp(ip, pool[index].end) <= 0) {
                    return true;
                }
            }
            return false;
        } catch (e) {
            return false;
        }
    }
};
