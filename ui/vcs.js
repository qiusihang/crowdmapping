var map, panorama, sv;
var records = new Array();
var records_number = 0;
var n_uoa = 0;
var current_uoa = 0;
var initialPos = new Array();
var innerCoords = new Array();
var innerCoordsVis = new Array();
var total_s = new Array();
var progress = new Array();
var last_inside_pos = null;
var poly;
var poly_line = new Array();
var flag_marker;
var lx = 0, ly = 0, rx = 0, ry = 0; // draw box
var log = "";
var userid = "";
// var server_url = "https://urbanmapping.tk/urbanmapping/";
var server_url = "http://145.100.58.129/urbanmapping/";

function initialize()
{
    userid = Date.now().toString(36) + Math.random().toString(36).substr(3,12);
    GetRequest();
}

function GetRequest() // get the initial position and the task region (polygon)
{
    var url = location.search;
    if (url.indexOf("?") != -1)
    {
        var str = url.substr(1);
        var strs = str.split("&");
        for ( var i = 0 ; i < strs.length ; i ++ )
        {
            var params = strs[i].split('=');
            if ( params.length < 2 ) continue;
            if ( params[0] == "utag"){
                userid = params[1] + userid;
            } else if ( params[0] == "init" && params[1] == "true"){
                jQuery.ajax({
                    dataType:"JSONP",
                    jsonp:"callback",
                    url:server_url+"tutorialinit.php",
                    data:{},
                    success:function(response){
                        n_uoa = parseInt(response['n']);
                        for (var j = 0 ; j < n_uoa ; j ++ )
                        {
                            initialPos[j] = GetStarting(response['start'+j]);
                            innerCoords[j] = GetPolygon(response['poly'+j]);
                            innerCoordsVis[j] = new Array();
                            for (var k = 0 ; k < innerCoords[j].length; k ++ )
                                innerCoordsVis[j][k] = false;
                        }
                        initUI();
                    },
                    error:function(e){
                        console.log("Initialization failed");
                    }
                });
            } else if ( params[0] == "test"){
                n_uoa = 1;
                sp = params[1].split('+');
                for (var j = 0 ; j < n_uoa ; j ++ )
                {
                    initialPos[j] = GetStarting(sp[0]);
                    innerCoords[j] = GetPolygon(sp[1]);
                    innerCoordsVis[j] = new Array();
                    for (var k = 0 ; k < innerCoords[j].length; k ++ )
                        innerCoordsVis[j][k] = false;
                }
                initUI();
            }
        }//end: search each params
    }
}

function addMarker(location)
{
    var marker = new google.maps.Marker({
        position: location,
        icon: "figs/step.png",
        map: map
    });
}

function addLabel(location)
{
    var marker = new google.maps.Marker({
        position: location,
        icon: "figs/object.png",
        map: map
    });
}

function GetStarting(param)
{
    var ip = {lat:0,lng:0};
    var nums = param.split("|");
    if (nums.length > 1)
    {
        ip.lat = parseFloat(nums[0]);
        ip.lng = parseFloat(nums[1]);
    }
    return ip;
}

function GetPolygon(param)
{
    var ic = new Array();
    var nums = param.split("|");
    if ( nums.length >= 6 )
    {
        for ( var j = 0 ; j < nums.length ; j +=2 )
        {
            if ( isNaN(parseFloat(nums[j])) || isNaN(parseFloat(nums[j+1])) ) continue;
            ic[j/2] = {lat:parseFloat(nums[j]),lng:parseFloat(nums[j+1])};
        }
        return ic;
    }
    return [];
}

function initUI()
{
    document.getElementById('street-view-loading').style.zIndex = 0;
    document.getElementById('uoa-condition').innerHTML = (current_uoa+1)+"/"+n_uoa;

    panorama = new google.maps.StreetViewPanorama(
        document.getElementById('street-view'), {
            position: initialPos[0],
            source: 'outdoor',
            radius: 10,
            pov: {heading: 180, pitch: 0},
            addressControl: false,
            fullscreenControl: false,
            motionTrackingControl: false,
            scrollwheel: false,
            linksControl: false
        }
    );

    panorama.setPosition(initialPos[0]);
    map = new google.maps.Map(
        document.getElementById('map'),
        {
            center: initialPos[0],
            fullscreenControl: false,
            mapTypeControl: false,
            zoomControl: false,
            zoom: 17
        }
    );
    map.setStreetView(panorama);
    flag_marker = new google.maps.Marker({
            position: initialPos[0],
            map: map,
            animation: google.maps.Animation.DROP,
            icon: "figs/beachflag.png",
            title: 'Starting Point'
        });

    // draw task-area
    // outerCoords: whole world (blue), clockwise
    // innerCoords: task-area (a hole), anticlockwise
    for (var i = 0 ; i < n_uoa ; i ++ )
    {
        progress[i] = 0;
        total_s[i] = 0;
        for (var j = 0 ; j < innerCoords[i].length ; j ++ )
        {
            total_s[i] = total_s[i] + get_distance(innerCoords[i][j], innerCoords[i][(j+1)%(innerCoords[i].length)]);
            //console.log(total_s[i]);
        }
        total_s[i] = total_s[i] / 2;
    }

    var outerCoords = [
        {lat: 90,lng:-90},{lat: 90,lng: 90},{lat: 90,lng:180},{lat: 90,lng:-90},
        {lat:-90,lng:-90},{lat:-90,lng:180},{lat:-90,lng: 90},{lat:-90,lng:-90}];

    if ( n_uoa > 0 )
    {
        var paths = new Array();
        paths[0] = outerCoords;
        for (var i = 0 ; i < n_uoa ; i ++ )
        {
            paths[i+1] = innerCoords[i]
            poly_line[i] = new google.maps.Polygon({
                paths: innerCoords[i],
                strokeColor: '#0000FF',
                strokeOpacity: 0.3,
                strokeWeight: 1,
                map: map,
                fillOpacity: 0.0
            });
        }
        poly = new google.maps.Polygon({
            paths: paths,
            strokeWeight: 0,
            map: map,
            fillColor: '#FF0000',
            fillOpacity: 0.3
        });
    }

    panorama.addListener('position_changed', function() {
        addlog("PANO CHANGED:"+panorama.getPosition()+"&"+panorama.getPov().heading+"&"+panorama.getPov().pitch+"&"+panorama.getZoom());
        map.setCenter(panorama.getPosition());
        var inside = false;
        for ( var i = 0 ; i < n_uoa ; i ++ )
        {
            if (google.maps.geometry.poly.containsLocation(panorama.getPosition(), poly_line[i]))
            {
                inside = true;
                break;
            }
        }
        if (inside)
        {
            // last_inside_pos = panorama.getPosition();
            addMarker(panorama.getPosition());
            update_progress(panorama.getPosition());
            warn("");
        }else{
            console.log("warn!");
            warn("WARNING:Please stay inside the task region.",true);
            // if (last_inside_pos != null) panorama.setPosition(last_inside_pos);  // bad idea
        }
    });
    document.getElementById('street-view').onmouseup = function()
    {
        addlog("PANO CHANGED:"+panorama.getPosition()+"&"+panorama.getPov().heading+"&"+panorama.getPov().pitch+"&"+panorama.getZoom());
    };
}

function get_distance(ll1, ll2)
{
    var x = (ll2.lng - ll1.lng) * 111300.0 * Math.cos(ll1.lat/180.0*Math.PI);
    var y = (ll2.lat - ll1.lat) * 111300.0;
    var d = Math.sqrt(x*x + y*y);
    if (isNaN(d)) return 0;
    return d;
}

var total_progress = 0;
function update_progress(cur_pos)
{
    var md = 0;
    for ( var i = 0 ; i < innerCoords[current_uoa].length ; i ++ )
    {
        d = get_distance({lat:cur_pos.lat(), lng:cur_pos.lng()}, innerCoords[current_uoa][i]);
        if ( d < 20 )
        {
            innerCoordsVis[current_uoa][i] = true;
        }else if (innerCoordsVis[current_uoa][i] == false){
            md = Math.max(md, d);
        }
    }
    progress[current_uoa] = Math.max(progress[current_uoa], total_s[current_uoa]-md);
    s1 = 0;
    s2 = 0;
    for ( var i = 0 ; i < n_uoa ; i ++ )
    {
        s1 += progress[i];
        s2 += total_s[i];
    }
    total_progress = s1/s2;
    document.getElementById('progress-percentage').innerHTML = parseInt(s1/s2*100+"")+"%";
    if (total_progress > 0.9 && records_number == 0)
        document.getElementById('submit_button').innerHTML = 'SUBMIT (NO TREE!)';
    w = parseInt(document.getElementById('progress').clientWidth) - 4;
    document.getElementById('progress-bar').style.right = parseInt(w + 2 - s1/s2*w + "") + "px";
}

function warn(content, highlight)   // show information at the bottom of the page
{
    var target = document.getElementById('warning');
    if ( highlight )
    {
        alert(content);
        target.style.color = "red";
    }else{
        target.style.color = "black";
    }
    target.innerHTML = content;
}

var log_count = 0;

function addlog(content)
{
    content = content + "&" + new Date();
    console.log(content);
    log += content+"###";

    log_count ++;
    if ( log_count > 2 )
    {
        var data = {userid:userid,log:log};
        var form = document.createElement("form");
        form.method = "get";
        form.action = server_url + "receive_log.php";
        form.target = "hidden_frame";
        for ( var k in data)
        {
            var pair = document.createElement("input");
            pair.setAttribute("name", k);
            pair.setAttribute("value", data[k]);
            form.appendChild(pair);
        }
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        console.log("Records autosaved.");
        log_count = 0;
        log = "";
    }
}

function get_request(record) // request a screenshot from Google server
{
    var size = "400x200";
    var location = record.location + "";
    location = location.substr(1,location.length-2);
    //var dbg = document.getElementById('instructionscontent');
    //dbg.innerHTML = location;
    var key = "AIzaSyA7MIhe-OZEx4An2EQKAmVVwKCR6VMqQQA";
    var request = "https://maps.googleapis.com/maps/api/streetview?size=" + size;
    request += "&location=" + location;
    request += "&heading=" + record.heading;
    request += "&pitch=" + record.pitch;
    request += "&fov=" + (180/Math.pow(2,record.zoom));
    request += "&key=" + key;
    return request;
}

function show_table() // update POI list
{
    var ss = document.getElementById('screenshots');
    var content = "";
    for ( var i = records_number-1 ; i >=0 ; i -- )
    {
        content += "<tr><td class=\"item_pic\">";
        request = get_request(records[i]);
        content += "<img width=\"100%\" src=\""+request+"\"/></td>";

        content += "<td class=\"item_text\"><b>&nbspLAT:<br/>&nbspLNG:&nbsp<br/>&nbspTIME:</b></td>";

        content += "<td class=\"item_text\">";
        var location = records[i].location + "";
        location = location.substr(1,location.length-2);
        latlon = location.split(" ");
        content += "&nbsp"+latlon[0].substr(0,10)+"&nbsp";
        content += "<br/>&nbsp"+latlon[1].substr(0,10)+"&nbsp";
        content += "<br/>&nbsp"+records[i].date.toLocaleTimeString()+"</td>";

        content += "<td class=\"item_text\">";
        content += "<input style=\"width:60px;background-color:#999999;color:#fff;border-radius:10px\" type=\"button\" id=\"loc"+i+"\" value=\"locate\" onclick=\"locate_func(this.id)\"><br/>";
        content += "<input style=\"width:60px;background-color:#999999;color:#fff;border-radius:10px\" type=\"button\" id=\"btn"+i+"\" value=\"remove\" onclick=\"remove_func(this.id)\">";
        content += "</td></tr>";
    }
    ss.innerHTML = "<table border=\"0\">"+content+"</table>";
}

function add_row(location,estimated_location,heading,pitch,zoom,box_left,box_top,box_right,box_bottom) // add a POI
{
    records[records_number] = {
        location:location,
        estimation:estimated_location,
        heading:heading,
        pitch:pitch,
        zoom:zoom,
        date:new Date(),
        box_left:box_left,
        box_top:box_top,
        box_right:box_right,
        box_bottom:box_bottom
    };
    log_count = 20; // force to save;
    addlog("ADD SHOT "+records_number+":"+location+"&"+heading+"&"+pitch+"&"+zoom+"&"+records[records_number].date+"&"+box_left+"&"+box_top+"&"+box_right+"&"+box_bottom);
    records_number ++;
    show_table();
    document.getElementById('submit_button').innerHTML = 'SUBMIT';
}

function back_func()
{
    var cvs = document.getElementById("street-view-canvas");
    cvs.style.zIndex = 0;
    document.getElementById("label").style.zIndex = 10;
    document.getElementById("back").style.zIndex = 0;
    addlog("BACK BUTTON");
}

function locate_func(btnid) // action of "locate" button
{
    var index = new Number(btnid.substr(3));
    panorama.setPosition(records[index].location);
    panorama.setPov({heading:records[index].heading, pitch:records[index].pitch});
    panorama.setZoom(records[index].zoom);

    var cvs = document.getElementById("street-view-canvas");
    cvs.style.zIndex = 9;
    cvs.width = document.getElementById('street-view').clientWidth;
    cvs.height = document.getElementById("street-view").clientHeight;
    var context = cvs.getContext('2d');
    var left = cvs.width * records[index].box_left;
    var top = cvs.height * records[index].box_top;
    var right = cvs.width * records[index].box_right;
    var bottom = cvs.height * records[index].box_bottom;
    context.strokeStyle="red";
    context.fillStyle="red";
    context.lineWidth = 2;
    context.rect(left,top,right-left,bottom-top);
    context.stroke();

    document.getElementById("back").style.zIndex = 10;
    document.getElementById("label").style.zIndex = 0;
    addlog("LOCATE BUTTON "+btnid);
    addlog("PANO CHANGED:"+panorama.getPosition()+"&"+panorama.getPov().heading+"&"+panorama.getPov().pitch+"&"+panorama.getZoom());
}

function remove_func(btnid) // action of "remove" button
{
    var index = new Number(btnid.substr(3));
    for ( var i = index + 1 ; i < records_number ; i ++ )
    {
        records[i-1] = records[i];
    }
    log_count = 20; // force to save;
    addlog("REMOVE BUTTON "+btnid);
    records_number --;
    if (total_progress > 0.9 && records_number == 0)
        document.getElementById('submit_button').innerHTML = 'SUBMIT (NO TREE!)';
    show_table();
}

function shot_func()
{
    var location = panorama.getPosition();
    var heading = panorama.getPov().heading;
    var pitch = panorama.getPov().pitch;
    var zoom = panorama.getZoom();

    // Let user draw a box on street view
    var cvs = document.getElementById("street-view-canvas");
    cvs.style.zIndex = 9;
    cvs.width = document.getElementById('street-view').clientWidth;
    cvs.height = document.getElementById("street-view").clientHeight;
    var context = cvs.getContext('2d');
    cvs.onmousedown = function(ev) //mouse down: set the startpoint of the rectangular
    {
        var ev = ev || window.event;
        var startx = (ev.clientX-cvs.offsetLeft)/cvs.width;
        var starty = (ev.clientY-cvs.offsetTop)/cvs.height;
        var currentx = startx;
        var currenty = starty;
        document.onmousemove = function(ev) //mouse move: draw rectangular
        {
            context.clearRect(0,0,cvs.width,cvs.height);
            //cvs.height = cvs.height; // clear the canvas
            var ev = ev || window.event;
            currentx = (ev.clientX-cvs.offsetLeft)/cvs.width;
            currenty = (ev.clientY-cvs.offsetTop)/cvs.height;
            if ( currenty < starty )
            {
                lx = Math.min(currentx,startx+startx-currentx);
                ly = currenty;
                rx = Math.max(currentx,startx+startx-currentx);
                ry = starty;
                var left = cvs.width * lx;
                var top = cvs.height * ly;
                var right = cvs.width * rx;
                var bottom = cvs.height * ry;
                context.strokeStyle="red";
                context.fillStyle="red";
                context.lineWidth = 2;
                context.beginPath();
                context.arc((left+right)/2, bottom, 10 ,0, 2*Math.PI, true);
                context.fill();
                context.rect(left,top,right-left,bottom-top);
                context.stroke();
            }
        };
        cvs.onmouseup = function() // mouse up: save shot
        {
            cvs.onmousedown = null;
            document.onmousemove = null;
            cvs.onmouseup = null;
            cvs.style.zIndex = 0;
            if ( currenty < starty )
            {
                var y = 1.0 - Math.max(ly,ry)*2.0;
                var x = (lx + rx) - 1.0;
                var fov = (180/Math.pow(2,zoom));
                var r = Raycast.createNew(heading, pitch, x, y, fov, cvs.width/cvs.height);
                var l = r.get_latlng(location.lat(),location.lng());
                if (l!=null) {
                    warn("The object is labeled.",false);
                    addLabel(l);
                    add_row(location,l,heading,pitch,zoom,lx,ly,rx,ry);
                }
                else warn("Unable to label the object. Please move closer to the object.",true);
            }
        };
    };
}

function pack_data()
{
    var data = {};
    data["userid"] = userid;
    data["number"] = records_number;
    for ( var i = 0 ; i < records_number ; i ++ )
    {
        data["location"+i] = records[i].location + "";
        data["estimation"+i] = records[i].estimation.lat + "," + records[i].estimation.lng;
        data["heading"+i] = records[i].heading + "";
        data["pitch"+i] = records[i].pitch + "";
        data["zoom"+i] = records[i].zoom + "";
        data["date"+i] = records[i].date + "";
        data["box_left"+i] = records[i].box_left + "";
        data["box_top"+i] = records[i].box_top + "";
        data["box_right"+i] = records[i].box_right + "";
        data["box_bottom"+i] = records[i].box_bottom + "";
    }
    return data;
}

function post_data() // action of "generate POI list" button
{
    if ( total_progress < 0.8 && records_number < 3 )
    {
       warn('Please label more trees.', true);
       return;
    }
    if ( total_progress < 0.8 )
    {
        warn('You should submit the result after task progress reaches at least 80%.', true);
        return;
    }
    data = pack_data();
    var form = document.createElement("form");
    form.method = "post";
    form.action = server_url + "receive_list.php";
    form.target = "hidden_frame";
    for ( var k in data)
    {
        var pair = document.createElement("input");
        pair.setAttribute("name", k);
        pair.setAttribute("value", data[k]);
        form.appendChild(pair);
    }
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);

    warn("Object list saved. Thank you! <b>Task Token:</b> <span style=\"background-color:yellow\"><i>"
    +userid+"</i></span>. You can continue exploring and submit the list again.",false);
    //+userid+"</i></span>. You can continue exploring and submit the list again. Click <a href=\""
    //+server_url+"show_list.php?userid="+userid+"\" target=\"_blank\">HERE</a> to review the list.",false);
}

var current_instruction_id = 0;

function previous_instruction()
{
    if ( current_instruction_id > 0 )
    {
        current_instruction_id -= 1;
        document.getElementById('tutorial_content').data = "instruction/instruction" + current_instruction_id +'.html';
        document.getElementById('progress-tutorial').innerHTML = current_instruction_id+"/7";
        document.getElementById('next_tutorial').innerHTML = "&#8594;";
    }
}

function next_instruction()
{
    if ( current_instruction_id < 7 )
    {
        current_instruction_id += 1;
        document.getElementById('tutorial_content').data = "instruction/instruction" + current_instruction_id +'.html';
        document.getElementById('progress-tutorial').innerHTML = current_instruction_id+"/7";
        if ( current_instruction_id == 7 )
            document.getElementById('next_tutorial').innerHTML = "&#215;";
        else
            document.getElementById('next_tutorial').innerHTML = "&#8594;";
    }else{
        document.getElementById('tutorial').style.visibility = "hidden";
    }
}

function close_instruction()
{
    document.getElementById('tutorial').style.visibility = "hidden";
}

function show_instruction()
{
    current_instruction_id = 0;
    document.getElementById('tutorial_content').data = "instruction/instruction" + current_instruction_id +'.html';
    document.getElementById('next_tutorial').innerHTML = "&#8594;";
    document.getElementById('tutorial').style.visibility = "visible";
    document.getElementById('progress-tutorial').innerHTML = "0/7";
}

document.getElementById('label').onclick = shot_func;
document.getElementById('back').onclick = back_func;
document.getElementById('next-uoa').onclick = function() {
    if (current_uoa < n_uoa-1)
    {
        current_uoa ++;
        back_func();
        document.getElementById('uoa-condition').innerHTML = (current_uoa+1)+"/"+n_uoa;
        panorama.setPosition(initialPos[current_uoa]);
        flag_marker.setPosition(initialPos[current_uoa]);
    }
};
document.getElementById('previous-uoa').onclick = function() {
    if (current_uoa > 0)
    {
        current_uoa --;
        back_func();
        document.getElementById('uoa-condition').innerHTML = (current_uoa+1)+"/"+n_uoa;
        panorama.setPosition(initialPos[current_uoa]);
        flag_marker.setPosition(initialPos[current_uoa]);
    }
};

window.addEventListener("resize",resizeCanvas,false);
function resizeCanvas()
{
    var cvs = document.getElementById("street-view-canvas");
    cvs.width = document.getElementById('street-view').clientWidth;
    cvs.height = document.getElementById("street-view").clientHeight;
    var context = cvs.getContext('2d');
    var left = cvs.width * lx;
    var top = cvs.height * ly;
    var right = cvs.width * rx;
    var bottom = cvs.height * ry;
    context.strokeStyle="red";
    context.rect(left,top,right-left,bottom-top);
    context.stroke();
}
