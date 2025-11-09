<script>
    var numbkle = [[5,5], [7,15], [13,7], [90,90], [93,73], [77,90], [10,91], [9,76], [18,92], [90,12], [80,8], [85,20]];
</script>

<style>
    #sparklid {
        background-color: transparent;
        height: 90vh;
        width: 100%;
        left: -10%;
        position: absolute;
    }
    .sparkle {
        image-rendering: pixelated;
        position: absolute;
        width: 7vmax;
        height: 7vmax;
        animation: 1s linear 1 both normal zoomin;
        animation-delay: 1.5s;
    }
    @keyframes swirl {
        from {
            transform: rotate(0%);
        }
        to {
            transform: rotate(359%);
        }
    }
    @keyframes zoomin {
        from {
            transform: scale(0.001);
        }
        to {
            transform: scale(1);
        }
    }
</style>

<div id="sparklid">
    {#each numbkle as numbs}
        <img class="sparkle" src="/assets/Sprite-Sparkle%20Hut!.gif" alt="sparkle!" style="left: {numbs[0]}%; top: {numbs[1]}%;">
    {/each}
</div>
