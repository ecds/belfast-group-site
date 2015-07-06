
function Ctrl($scope) {
    // $scope.swatch = [
    //     {
    //         hexVal: '#e9a354',
    //         shade: function(){
    //             return ColorLuminance(this.hexVal, -.25);
    //         }
    //     },
    //     {
    //         hexVal: '#f6ecdd',
    //         shade: function(){
    //             return ColorLuminance(this.hexVal, -.25);
    //         }
    //     },
    //     {
    //         hexVal: '#b8cbef',
    //         shade: function(){
    //             return ColorLuminance(this.hexVal, -.25);
    //         }
    //     },
    //     {
    //         hexVal: '#0053b8',
    //         shade: function(){
    //             return ColorLuminance(this.hexVal, -.25);
    //        }
    //     }
    // ];

    /* Output for Angular.js */
    $scope.swatch = [

    {
        hexVal: '#4e4e4e',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#e8e8e8',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#c2dbe5',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#1fa7e4',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#fee07c',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#4193cc',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#5bc15b',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    },

    {
        hexVal: '#99000a',
        shade: function(){
            return ColorLuminance(this.hexVal, -.25);
        }
    }
    ];

$scope.fonts = [
{name:'Arial Black', type:'Sans'},
{name:'Arial', type:'Sans'},
{name:'Times New Roman', type:'Serif'},
{name:'Georgia', type:'Serif'},
{name:'Courier New', type:'Serif'},
{name:'Abel', type:'Sans'},{name:'Abril Fatface', type:'Cursive'},{name:'Aclonica', type:'Sans'},{name:'Actor', type:'Sans'},{name:'Adamina', type:'Serif'},{name:'Aguafina Script', type:'Cursive'},{name:'Aladin', type:'Cursive'},{name:'Aldrich', type:'Sans'},{name:'Alice', type:'Serif'},{name:'Alike Angular', type:'Serif'},{name:'Alike', type:'Serif'},{name:'Allan', type:'Cursive'},{name:'Allerta Stencil', type:'Sans'},{name:'Allerta', type:'Sans'},{name:'Amaranth', type:'Sans'},{name:'Amatic SC', type:'Cursive'},{name:'Andada', type:'Serif'},{name:'Andika', type:'Sans'},{name:'Annie Use Your Telescope', type:'Cursive'},{name:'Anonymous Pro', type:'Sans'},{name:'Antic', type:'Sans'},{name:'Anton', type:'Sans'},{name:'Arapey', type:'Serif'},{name:'Architects Daughter', type:'Cursive'},{name:'Arimo', type:'Sans'},{name:'Artifika', type:'Serif'},{name:'Arvo', type:'Serif'},{name:'Asset', type:'Cursive'},{name:'Astloch', type:'Cursive'},{name:'Atomic Age', type:'Cursive'},{name:'Aubrey', type:'Cursive'},{name:'Bangers', type:'Cursive'},{name:'Bentham', type:'Serif'},{name:'Bevan', type:'Serif'},{name:'Bigshot One', type:'Cursive'},{name:'Bitter', type:'Serif'},{name:'Black Ops One', type:'Cursive'},{name:'Bowlby One SC', type:'Sans'},{name:'Bowlby One', type:'Sans'},{name:'Brawler', type:'Serif'},{name:'Bubblegum Sans', type:'Cursive'},{name:'Buda', type:'Sans'},{name:'Butcherman Caps', type:'Cursive'},{name:'Cabin Condensed', type:'Sans'},{name:'Cabin Sketch', type:'Cursive'},{name:'Cabin', type:'Sans'},{name:'Cagliostro', type:'Sans'},{name:'Calligraffitti', type:'Cursive'},{name:'Candal', type:'Sans'},{name:'Cantarell', type:'Sans'},{name:'Cardo', type:'Serif'},{name:'Carme', type:'Sans'},{name:'Carter One', type:'Sans'},{name:'Caudex', type:'Serif'},{name:'Cedarville Cursive', type:'Cursive'},{name:'Changa One', type:'Cursive'},{name:'Cherry Cream Soda', type:'Cursive'},{name:'Chewy', type:'Cursive'},{name:'Chicle', type:'Cursive'},{name:'Chivo', type:'Sans'},{name:'Coda Caption', type:'Sans'},{name:'Coda', type:'Cursive'},{name:'Comfortaa', type:'Cursive'},{name:'Coming Soon', type:'Cursive'},{name:'Contrail One', type:'Cursive'},{name:'Convergence', type:'Sans'},{name:'Cookie', type:'Cursive'},{name:'Copse', type:'Serif'},{name:'Corben', type:'Cursive'},{name:'Cousine', type:'Sans'},{name:'Coustard', type:'Serif'},{name:'Covered By Your Grace', type:'Cursive'},{name:'Crafty Girls', type:'Cursive'},{name:'Creepster Caps', type:'Cursive'},{name:'Crimson Text', type:'Serif'},{name:'Crushed', type:'Cursive'},{name:'Cuprum', type:'Sans'},{name:'Damion', type:'Cursive'},{name:'Dancing Script', type:'Cursive'},{name:'Dawning of a New Day', type:'Cursive'},{name:'Days One', type:'Sans'},{name:'Delius Swash Caps', type:'Cursive'},{name:'Delius Unicase', type:'Cursive'},{name:'Delius', type:'Cursive'},{name:'Devonshire', type:'Cursive'},{name:'Didact Gothic', type:'Sans'},{name:'Dorsa', type:'Sans'},{name:'Dr Sugiyama', type:'Cursive'},{name:'Droid Sans Mono', type:'Sans'},{name:'Droid Sans', type:'Sans'},{name:'Droid Serif', type:'Serif'},{name:'EB Garamond', type:'Serif'},{name:'Eater Caps', type:'Cursive'},{name:'Expletus Sans', type:'Cursive'},{name:'Fanwood Text', type:'Serif'},{name:'Federant', type:'Cursive'},{name:'Federo', type:'Sans'},{name:'Fjord One', type:'Serif'},{name:'Fondamento', type:'Cursive'},{name:'Fontdiner Swanky', type:'Cursive'},{name:'Forum', type:'Cursive'},{name:'Francois One', type:'Sans'},{name:'Gentium Basic', type:'Serif'},{name:'Gentium Book Basic', type:'Serif'},{name:'Geo', type:'Sans'},{name:'Geostar Fill', type:'Cursive'},{name:'Geostar', type:'Cursive'},{name:'Give You Glory', type:'Cursive'},{name:'Gloria Hallelujah', type:'Cursive'},{name:'Goblin One', type:'Cursive'},{name:'Gochi Hand', type:'Cursive'},{name:'Goudy Bookletter 1911', type:'Serif'},{name:'Gravitas One', type:'Cursive'},{name:'Gruppo', type:'Sans'},{name:'Hammersmith One', type:'Sans'},{name:'Herr Von Muellerhoff', type:'Cursive'},{name:'Holtwood One SC', type:'Serif'},{name:'Homemade Apple', type:'Cursive'},{name:'IM Fell DW Pica SC', type:'Serif'},{name:'IM Fell DW Pica', type:'Serif'},{name:'IM Fell Double Pica SC', type:'Serif'},{name:'IM Fell Double Pica', type:'Serif'},{name:'IM Fell English SC', type:'Serif'},{name:'IM Fell English', type:'Serif'},{name:'IM Fell French Canon SC', type:'Serif'},{name:'IM Fell French Canon', type:'Serif'},{name:'IM Fell Great Primer SC', type:'Serif'},{name:'IM Fell Great Primer', type:'Serif'},{name:'Iceland', type:'Cursive'},{name:'Inconsolata', type:'Sans'},{name:'Indie Flower', type:'Cursive'},{name:'Irish Grover', type:'Cursive'},{name:'Istok Web', type:'Sans'},{name:'Jockey One', type:'Sans'},{name:'Josefin Sans', type:'Sans'},{name:'Josefin Slab', type:'Serif'},{name:'Judson', type:'Serif'},{name:'Julee', type:'Cursive'},{name:'Jura', type:'Sans'},{name:'Just Another Hand', type:'Cursive'},{name:'Just Me Again Down Here', type:'Cursive'},{name:'Kameron', type:'Serif'},{name:'Kelly Slab', type:'Cursive'},{name:'Kenia', type:'Sans'},{name:'Knewave', type:'Cursive'},{name:'Kranky', type:'Cursive'},{name:'Kreon', type:'Serif'},{name:'Kristi', type:'Cursive'},{name:'La Belle Aurore', type:'Cursive'},{name:'Lancelot', type:'Cursive'},{name:'Lato', type:'Sans'},{name:'League Script', type:'Cursive'},{name:'Leckerli One', type:'Cursive'},{name:'Lekton', type:'Sans'},{name:'Lemon', type:'Cursive'},{name:'Limelight', type:'Cursive'},{name:'Linden Hill', type:'Serif'},{name:'Lobster Two', type:'Cursive'},{name:'Lobster', type:'Cursive'},{name:'Lora', type:'Serif'},{name:'Love Ya Like A Sister', type:'Cursive'},{name:'Loved by the King', type:'Cursive'},{name:'Luckiest Guy', type:'Cursive'},{name:'Maiden Orange', type:'Cursive'},{name:'Mako', type:'Sans'},{name:'Marck Script', type:'Cursive'},{name:'Marvel', type:'Sans'},{name:'Mate SC', type:'Serif'},{name:'Mate', type:'Serif'},{name:'Maven Pro', type:'Sans'},{name:'Meddon', type:'Cursive'},{name:'MedievalSharp', type:'Cursive'},{name:'Megrim', type:'Cursive'},{name:'Merienda One', type:'Cursive'},{name:'Merriweather', type:'Serif'},{name:'Metrophobic', type:'Sans'},{name:'Michroma', type:'Sans'},{name:'Miltonian Tattoo', type:'Cursive'},{name:'Miltonian', type:'Cursive'},{name:'Miss Fajardose', type:'Cursive'},{name:'Miss Saint Delafield', type:'Cursive'},{name:'Modern Antiqua', type:'Cursive'},{name:'Molengo', type:'Sans'},{name:'Monofett', type:'Cursive'},{name:'Monoton', type:'Cursive'},{name:'Monsieur La Doulaise', type:'Cursive'},{name:'Montez', type:'Cursive'},{name:'Mountains of Christmas', type:'Cursive'},{name:'Mr Bedford', type:'Cursive'},{name:'Mr Dafoe', type:'Cursive'},{name:'Mr De Haviland', type:'Cursive'},{name:'Mrs Sheppards', type:'Cursive'},{name:'Muli', type:'Sans'},{name:'Neucha', type:'Cursive'},{name:'Neuton', type:'Serif'},{name:'News Cycle', type:'Sans'},{name:'Niconne', type:'Cursive'},{name:'Nixie One', type:'Cursive'},{name:'Nobile', type:'Sans'},{name:'Nosifer Caps', type:'Cursive'},{name:'Nothing You Could Do', type:'Cursive'},{name:'Nova Cut', type:'Cursive'},{name:'Nova Flat', type:'Cursive'},{name:'Nova Mono', type:'Cursive'},{name:'Nova Oval', type:'Cursive'},{name:'Nova Round', type:'Cursive'},{name:'Nova Script', type:'Cursive'},{name:'Nova Slim', type:'Cursive'},{name:'Nova Square', type:'Cursive'},{name:'Numans', type:'Sans'},{name:'Nunito', type:'Sans'},{name:'Old Standard TT', type:'Serif'},{name:'Open Sans Condensed', type:'Sans'},{name:'Open Sans', type:'Sans'},{name:'Orbitron', type:'Sans'},{name:'Oswald', type:'Sans'},{name:'Over the Rainbow', type:'Cursive'},{name:'Ovo', type:'Serif'},{name:'PT Sans Caption', type:'Sans'},{name:'PT Sans Narrow', type:'Sans'},{name:'PT Sans', type:'Sans'},{name:'PT Serif Caption', type:'Serif'},{name:'PT Serif', type:'Serif'},{name:'PT Mono', type:'Serif'},{name:'Pacifico', type:'Cursive'},{name:'Passero One', type:'Cursive'},{name:'Patrick Hand', type:'Cursive'},{name:'Paytone One', type:'Sans'},{name:'Permanent Marker', type:'Cursive'},{name:'Petrona', type:'Serif'},{name:'Philosopher', type:'Sans'},{name:'Piedra', type:'Cursive'},{name:'Pinyon Script', type:'Cursive'},{name:'Play', type:'Sans'},{name:'Playfair Display', type:'Serif'},{name:'Podkova', type:'Serif'},{name:'Poller One', type:'Cursive'},{name:'Poly', type:'Serif'},{name:'Pompiere', type:'Cursive'},{name:'Prata', type:'Serif'},{name:'Prociono', type:'Serif'},{name:'Puritan', type:'Sans'},{name:'Quattrocento Sans', type:'Sans'},{name:'Quattrocento', type:'Serif'},{name:'Questrial', type:'Sans'},{name:'Quicksand', type:'Sans'},{name:'Radley', type:'Serif'},{name:'Raleway', type:'Cursive'},{name:'Rammetto One', type:'Cursive'},{name:'Rancho', type:'Cursive'},{name:'Rationale', type:'Sans'},{name:'Redressed', type:'Cursive'},{name:'Reenie Beanie', type:'Cursive'},{name:'Ribeye Marrow', type:'Cursive'},{name:'Ribeye', type:'Cursive'},{name:'Righteous', type:'Cursive'},{name:'Rochester', type:'Cursive'},{name:'Rock Salt', type:'Cursive'},{name:'Rokkitt', type:'Serif'},{name:'Rosario', type:'Sans'},{name:'Ruslan Display', type:'Cursive'},{name:'Salsa', type:'Cursive'},{name:'Sancreek', type:'Cursive'},{name:'Sansita One', type:'Cursive'},{name:'Satisfy', type:'Cursive'},{name:'Schoolbell', type:'Cursive'},{name:'Shadows Into Light', type:'Cursive'},{name:'Shanti', type:'Sans'},{name:'Short Stack', type:'Cursive'},{name:'Sigmar One', type:'Sans'},{name:'Signika Negative', type:'Sans'},{name:'Signika', type:'Sans'},{name:'Six Caps', type:'Sans'},{name:'Slackey', type:'Cursive'},{name:'Smokum', type:'Cursive'},{name:'Smythe', type:'Cursive'},{name:'Sniglet', type:'Cursive'},{name:'Snippet', type:'Sans'},{name:'Sorts Mill Goudy', type:'Serif'},{name:'Special Elite', type:'Cursive'},{name:'Spinnaker', type:'Sans'},{name:'Spirax', type:'Cursive'},{name:'Stardos Stencil', type:'Cursive'},{name:'Sue Ellen Francisco', type:'Cursive'},{name:'Sunshiney', type:'Cursive'},{name:'Supermercado One', type:'Cursive'},{name:'Swanky and Moo Moo', type:'Cursive'},{name:'Syncopate', type:'Sans'},{name:'Tangerine', type:'Cursive'},{name:'Tenor Sans', type:'Sans'},{name:'Terminal Dosis', type:'Sans'},{name:'The Girl Next Door', type:'Cursive'},{name:'Tienne', type:'Serif'},{name:'Tinos', type:'Serif'},{name:'Tulpen One', type:'Cursive'},{name:'Ubuntu Condensed', type:'Sans'},{name:'Ubuntu Mono', type:'Sans'},{name:'Ubuntu', type:'Sans'},{name:'Ultra', type:'Serif'},{name:'UnifrakturCook', type:'Cursive'},{name:'UnifrakturMaguntia', type:'Cursive'},{name:'Unkempt', type:'Cursive'},{name:'Unlock', type:'Cursive'},{name:'Unna', type:'Serif'},{name:'VT323', type:'Cursive'},{name:'Varela Round', type:'Sans'},{name:'Varela', type:'Sans'},{name:'Vast Shadow', type:'Cursive'},{name:'Vibur', type:'Cursive'},{name:'Vidaloka', type:'Serif'},{name:'Volkhov', type:'Serif'},{name:'Vollkorn', type:'Serif'},{name:'Voltaire', type:'Sans'},{name:'Waiting for the Sunrise', type:'Cursive'},{name:'Wallpoet', type:'Cursive'},{name:'Walter Turncoat', type:'Cursive'},{name:'Wire One', type:'Sans'},{name:'Yanone Kaffeesatz', type:'Sans'},{name:'Yellowtail', type:'Cursive'},{name:'Yeseva One', type:'Serif'},{name:'Zeyada', type:'Cursive'}

];
$scope.font_weights = [
{name:'thin', value:100},
{name:'light', value:300},
{name:'normal',value:400},
{name:'bold', value:'bold'}
]
$scope.transform = [

]
$scope.current0 = $scope.fonts[0];
$scope.current1 = $scope.fonts[1];
$scope.current2 = $scope.fonts[2];

$scope.current_weight0 = $scope.font_weights[3];
$scope.current_weight1 = $scope.font_weights[2];
$scope.current_weight2 = $scope.font_weights[2];


$scope.current_weight0 = $scope.font_weights[1];
$scope.current0 = {"name":"Droid Serif","type":"Serif"};
$scope.current1 = {"name":"Droid Serif","type":"Serif"};
$scope.current2 = {"name":"Droid Serif","type":"Serif"};


function ColorLuminance(hex, lum) {
        // validate hex string
        hex = String(hex).replace(/[^0-9a-f]/gi, '');
        if (hex.length < 6) {
            hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        }
        lum = lum || 0;

        // convert to decimal and change luminosity
        var rgb = "#",
        c, i;
        for (i = 0; i < 3; i++) {
            c = parseInt(hex.substr(i * 2, 2), 16);
            c = Math.round(Math.min(Math.max(0, c + (c * lum)), 255)).toString(16);
            rgb += ("00" + c).substr(c.length);
        }

        return rgb;
    }

    function hex2rgb(hex){
        R = hexToR(hex);
        G = hexToG(hex);
        B = hexToB(hex);

        function hexToR(h) {return parseInt((cutHex(h)).substring(0,2),16)}
        function hexToG(h) {return parseInt((cutHex(h)).substring(2,4),16)}
        function hexToB(h) {return parseInt((cutHex(h)).substring(4,6),16)}
        function cutHex(h) {return (h.charAt(0)=="#") ? h.substring(1,7):h}

        return ([R,G,B]);
    }

    $scope.toRGB = function(hex){
        var rgbArray = hex2rgb(hex),
        R = rgbArray[0],
        G = rgbArray[1],
        B = rgbArray[2];

        rgb_str = "rgb("+R+","+G+","+B+")";
        return rgb_str;
    }

    $scope.correctContrast = function(hex){
        var rgbArray = hex2rgb(hex),
        R = rgbArray[0],
        G = rgbArray[1],
        B = rgbArray[2],
        text_color = "rgb("+R+","+G+","+B+")";
        if( R < 89 && G < 80 && B < 100){
            text_color = "rgba(255,255,255,0.5)";
        }

        return text_color;
    }

}