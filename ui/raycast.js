/**
 * @author sihang / http://github.com/qiusihang
 */

var Raycast = {

    createNew: function(heading, pitch, norm_screen_x, norm_screen_y, fov, aspect)
    {
        var raycast = {};
        raycast.heading = heading;
        raycast.pitch = pitch;
        raycast.screen_x = norm_screen_x;
        raycast.screen_y = norm_screen_y;
        raycast.fov = fov;
        raycast.aspect = aspect;

        raycast.get_raycast = function()
        {
            return {pitch: raycast.pitch + 0.5 * raycast.screen_y * raycast.fov / raycast.aspect,
                    heading: raycast.heading + 0.5 * raycast.screen_x * raycast.fov}
        }
        raycast.get_distance = function(observer_height)
        {
            var theta = raycast.get_raycast().pitch;
            if ( -1 > theta && theta > -89 )
                return Math.abs(observer_height/Math.tan(theta/180.0*Math.PI));
            else
                return null;
        }
        raycast.get_latlng = function(current_lat, current_lng)
        {
            var heading = ((360 - raycast.get_raycast().heading) + 90)%360;
            var distance = raycast.get_distance(2);
            if (distance == null || distance > 30) return null;
            var x = distance * Math.cos(heading/180.0*Math.PI);
            var y = distance * Math.sin(heading/180.0*Math.PI);
            return {lat: current_lat + y/111300.0,
                    lng: current_lng + x/111300.0/Math.cos(current_lat/180.0*Math.PI)};
        }

        return raycast;
    }

}
