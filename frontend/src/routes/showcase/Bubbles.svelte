<script>
    var numble = new Array(75);
    var numblig = new Array(50);
</script>

<style>
    #bubblid {
        background-color: transparent;
        height: 100%;
        width: 100%;
        float: left;
        position: fixed;
        z-index: 10;
    }
    .bubble {
        image-rendering: pixelated;
        position: absolute;
        top: 150vh;
        animation: 3s linear 1 both normal rise,
            0.5s linear infinite alternate sway,
            0.22s linear infinite alternate warp;
        width: 10vmax;
        height: 10vmax;
        z-index: 8;
    }
    .bubblig {
        image-rendering: pixelated;
        position: absolute;
        top: 150vh;
        animation: 2.5s linear 1 both normal rise,
            0.5s linear infinite alternate sway,
            0.3s linear infinite alternate warp;
        width: 30vmax;
        height: 30vmax;
        z-index: 6;
    }
    #sponge {
        image-rendering: pixelated;
        position: absolute;
        left: -50vw;
        top: 20vh;
        animation: 6s linear 1 both normal slide,
            0.7s linear infinite alternate bob;
        width: 30vmax;
        height: 30vmax;
        z-index: 9;
    }
    @keyframes rise {
        from {
            top: 150vh;
        }
        to {
            top: -80vh;
        }
    }
    @keyframes sway {
        from {
            transform: translate(0%);
        }
        to {
            transform: translate(10%);
        }
    }
    @keyframes warp {
        from {
            transform: skew(20deg, -10deg);
        }
        to {
            transform: skew(-10deg, -20deg);
        }
    }
    @keyframes slide {
        from {
            left: -50vw;
        }
        to {
            left: 150vmax;
        }
    }
    @keyframes bob {
        from {
            transform: translate(0%) skew(25deg, -10deg);
        }
        to {
            transform: translate(0%, 20%) skew(-10deg, -20deg);
        }
    }
</style>

<div id="bubblid">
    {#each numblig as _, numb}
        <img class="bubblig" src="/assets/Sprite-Bubble.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()*0.5}s">
        <img class="bubblig" src="/assets/Sprite-Bubble2.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()}s">
        <img class="bubblig" src="/assets/Sprite-Bubble3.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()}s">
    {/each}
    {#each numble as _, numb}
        <img class="bubble" src="/assets/Sprite-Bubble.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
        <img class="bubble" src="/assets/Sprite-Bubble2.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
        <img class="bubble" src="/assets/Sprite-Bubble3.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
    {/each}
    <img id="sponge" src="/assets/Sprite-Sponge.gif" alt="sponge!">
</div>
